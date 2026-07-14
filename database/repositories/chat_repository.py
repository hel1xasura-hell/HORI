"""Repository providing data-access methods for chat settings."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.chat import Chat

logger = get_logger(__name__)


class ChatRepository:
    """Encapsulates all read/write operations for the `chats` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["chats"]

    async def get_or_create(self, chat_id: int, title: str = "") -> Chat:
        """Fetch a chat's settings, creating a default record if none exists.

        Args:
            chat_id: The Telegram chat ID.
            title: The chat title to store if a new record is created.

        Returns:
            The existing or newly created `Chat` instance.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"chat_id": chat_id})
            if document is not None:
                return Chat.from_document(document)

            chat = Chat(chat_id=chat_id, title=title)
            await self._collection.insert_one(chat.to_document())
            logger.info("Created new chat settings record for chat_id=%s", chat_id)
            return chat
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to get or create chat {chat_id}: {exc}") from exc

    async def update_settings(self, chat_id: int, updates: Dict[str, Any]) -> None:
        """Apply a partial update to a chat's settings.

        Args:
            chat_id: The Telegram chat ID to update.
            updates: A mapping of field names to new values.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        updates = {**updates, "updated_at": datetime.now(timezone.utc)}
        try:
            await self._collection.update_one(
                {"chat_id": chat_id}, {"$set": updates}, upsert=True
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to update chat {chat_id}: {exc}") from exc

    async def set_title(self, chat_id: int, title: str) -> None:
        """Update the cached title for a chat.

        Args:
            chat_id: The Telegram chat ID.
            title: The new chat title.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        await self.update_settings(chat_id, {"title": title})

    async def delete(self, chat_id: int) -> None:
        """Remove a chat's settings record entirely.

        Args:
            chat_id: The Telegram chat ID to remove.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.delete_one({"chat_id": chat_id})
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to delete chat {chat_id}: {exc}") from exc

    async def count_all(self) -> int:
        """Return the total number of chats the bot has settings for.

        Returns:
            The number of documents in the `chats` collection.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            return await self._collection.count_documents({})
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to count chats: {exc}") from exc
