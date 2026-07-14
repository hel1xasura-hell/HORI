"""Repository providing data-access methods for private-chat connections."""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.connection import Connection

logger = get_logger(__name__)


class ConnectionRepository:
    """Encapsulates all read/write operations for the `connections` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["connections"]

    async def connect(self, user_id: int, chat_id: int) -> None:
        """Link a user's private chat to a group for remote management.

        Args:
            user_id: The Telegram user ID initiating the connection.
            chat_id: The group chat ID to connect to.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"user_id": user_id}, {"$set": {"chat_id": chat_id}}, upsert=True
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to connect user {user_id} to chat {chat_id}: {exc}") from exc

    async def get_connected_chat(self, user_id: int) -> Optional[int]:
        """Fetch the chat ID a user is currently connected to, if any.

        Args:
            user_id: The Telegram user ID to look up.

        Returns:
            The connected chat ID, or None if not connected.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"user_id": user_id})
            return document["chat_id"] if document else None
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fetch connection for user {user_id}: {exc}") from exc

    async def disconnect(self, user_id: int) -> bool:
        """Remove a user's active connection, if any.

        Args:
            user_id: The Telegram user ID to disconnect.

        Returns:
            True if a connection was removed, False if none existed.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            result = await self._collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to disconnect user {user_id}: {exc}") from exc
