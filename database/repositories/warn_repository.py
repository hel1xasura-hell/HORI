"""Repository providing data-access methods for user warnings."""

from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.warn import Warn

logger = get_logger(__name__)


class WarnRepository:
    """Encapsulates all read/write operations for the `warns` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["warns"]

    async def get(self, chat_id: int, user_id: int) -> Warn:
        """Fetch a user's warning record, returning an empty one if none exists.

        Args:
            chat_id: The chat to look up warnings for.
            user_id: The warned user's Telegram ID.

        Returns:
            The existing or a freshly initialized `Warn` instance.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"chat_id": chat_id, "user_id": user_id})
            if document is not None:
                return Warn.from_document(document)
            return Warn(chat_id=chat_id, user_id=user_id)
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fetch warns for user {user_id} in chat {chat_id}: {exc}") from exc

    async def add_warning(self, chat_id: int, user_id: int, reason: str) -> Warn:
        """Increment a user's warning count and record the reason.

        Args:
            chat_id: The chat the warning applies to.
            user_id: The warned user's Telegram ID.
            reason: A human-readable reason for the warning.

        Returns:
            The updated `Warn` instance after the increment.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one_and_update(
                {"chat_id": chat_id, "user_id": user_id},
                {
                    "$inc": {"count": 1},
                    "$push": {"reasons": reason},
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                },
                upsert=True,
                return_document=True,
            )
            return Warn.from_document(document)
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to add warning for user {user_id} in chat {chat_id}: {exc}") from exc

    async def reset(self, chat_id: int, user_id: int) -> None:
        """Reset a user's warning count and history to zero.

        Args:
            chat_id: The chat to reset warnings for.
            user_id: The user whose warnings should be reset.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"count": 0, "reasons": [], "updated_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to reset warnings for user {user_id} in chat {chat_id}: {exc}") from exc

    async def remove_one_warning(self, chat_id: int, user_id: int) -> Warn:
        """Remove a single warning from a user, without going below zero.

        Args:
            chat_id: The chat to modify warnings for.
            user_id: The user whose warning count should be decremented.

        Returns:
            The updated `Warn` instance after the decrement.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        current = await self.get(chat_id, user_id)
        new_count = max(0, current.count - 1)
        new_reasons = current.reasons[:-1] if current.reasons else []
        try:
            document = await self._collection.find_one_and_update(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"count": new_count, "reasons": new_reasons, "updated_at": datetime.now(timezone.utc)}},
                upsert=True,
                return_document=True,
            )
            return Warn.from_document(document)
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to remove warning for user {user_id} in chat {chat_id}: {exc}") from exc
