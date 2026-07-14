"""Repository providing data-access methods for federations."""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.federation import Federation

logger = get_logger(__name__)


class FederationRepository:
    """Encapsulates all read/write operations for the `federations` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["federations"]

    async def create(self, federation: Federation) -> None:
        """Persist a newly created federation.

        Args:
            federation: The `Federation` instance to insert.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.insert_one(federation.to_document())
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to create federation '{federation.name}': {exc}") from exc

    async def get_by_id(self, federation_id: str) -> Optional[Federation]:
        """Fetch a federation by its unique ID.

        Args:
            federation_id: The federation's unique identifier.

        Returns:
            The matching `Federation`, or None if not found.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"federation_id": federation_id})
            return Federation.from_document(document) if document else None
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fetch federation {federation_id}: {exc}") from exc

    async def get_by_chat(self, chat_id: int) -> Optional[Federation]:
        """Fetch the federation a chat currently belongs to, if any.

        Args:
            chat_id: The Telegram chat ID to search for.

        Returns:
            The matching `Federation`, or None if the chat is unaffiliated.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"chat_ids": chat_id})
            return Federation.from_document(document) if document else None
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fetch federation for chat {chat_id}: {exc}") from exc

    async def add_chat(self, federation_id: str, chat_id: int) -> None:
        """Add a chat to a federation.

        Args:
            federation_id: The federation to join.
            chat_id: The chat ID to add.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"federation_id": federation_id}, {"$addToSet": {"chat_ids": chat_id}}
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to add chat {chat_id} to federation {federation_id}: {exc}") from exc

    async def remove_chat(self, federation_id: str, chat_id: int) -> None:
        """Remove a chat from a federation.

        Args:
            federation_id: The federation to leave.
            chat_id: The chat ID to remove.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"federation_id": federation_id}, {"$pull": {"chat_ids": chat_id}}
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to remove chat {chat_id} from federation {federation_id}: {exc}") from exc

    async def ban_user(self, federation_id: str, user_id: int) -> None:
        """Add a user to a federation's banned user list.

        Args:
            federation_id: The federation to ban the user from.
            user_id: The Telegram user ID to ban.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"federation_id": federation_id}, {"$addToSet": {"banned_user_ids": user_id}}
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fban user {user_id} in federation {federation_id}: {exc}") from exc

    async def unban_user(self, federation_id: str, user_id: int) -> None:
        """Remove a user from a federation's banned user list.

        Args:
            federation_id: The federation to unban the user from.
            user_id: The Telegram user ID to unban.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"federation_id": federation_id}, {"$pull": {"banned_user_ids": user_id}}
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to unfban user {user_id} in federation {federation_id}: {exc}") from exc
