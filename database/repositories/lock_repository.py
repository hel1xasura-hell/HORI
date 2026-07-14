"""Repository providing data-access methods for chat content locks."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.lock import ChatLocks

logger = get_logger(__name__)


class LockRepository:
    """Encapsulates all read/write operations for the `locks` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["locks"]

    async def get(self, chat_id: int) -> ChatLocks:
        """Fetch the active locks for a chat, defaulting to none configured.

        Args:
            chat_id: The chat to fetch locks for.

        Returns:
            The existing or a freshly initialized `ChatLocks` instance.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"chat_id": chat_id})
            if document is not None:
                return ChatLocks.from_document(document)
            return ChatLocks(chat_id=chat_id)
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fetch locks for chat {chat_id}: {exc}") from exc

    async def lock(self, chat_id: int, lock_type: str) -> None:
        """Add a content type to the set of locked types for a chat.

        Args:
            chat_id: The chat to modify.
            lock_type: The `LockableType` value to lock, as a string.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": chat_id}, {"$addToSet": {"locked_types": lock_type}}, upsert=True
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to lock '{lock_type}' in chat {chat_id}: {exc}") from exc

    async def unlock(self, chat_id: int, lock_type: str) -> None:
        """Remove a content type from the set of locked types for a chat.

        Args:
            chat_id: The chat to modify.
            lock_type: The `LockableType` value to unlock, as a string.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": chat_id}, {"$pull": {"locked_types": lock_type}}, upsert=True
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to unlock '{lock_type}' in chat {chat_id}: {exc}") from exc

    async def unlock_all(self, chat_id: int) -> None:
        """Clear all locks configured for a chat.

        Args:
            chat_id: The chat to clear locks for.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": chat_id}, {"$set": {"locked_types": []}}, upsert=True
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to unlock all in chat {chat_id}: {exc}") from exc
