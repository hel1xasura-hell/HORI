"""Repository providing data-access methods for antispam flood tracking."""

from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.flood import FloodControl

logger = get_logger(__name__)


class FloodRepository:
    """Encapsulates all read/write operations for the `flood_control` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["flood_control"]

    async def register_message(self, chat_id: int, user_id: int, window_seconds: int) -> FloodControl:
        """Register a new message from a user, resetting the window if expired.

        Args:
            chat_id: The chat the message was sent in.
            user_id: The Telegram user ID of the sender.
            window_seconds: The duration, in seconds, of the flood-detection window.

        Returns:
            The updated `FloodControl` record after registering the message.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        now = datetime.now(timezone.utc)
        try:
            document = await self._collection.find_one({"chat_id": chat_id, "user_id": user_id})
            if document is None:
                record = FloodControl(chat_id=chat_id, user_id=user_id, message_count=1, window_started_at=now)
                await self._collection.insert_one(record.to_document())
                return record

            existing = FloodControl.from_document(document)
            elapsed = (now - existing.window_started_at.replace(tzinfo=timezone.utc)).total_seconds()

            if elapsed > window_seconds:
                existing.message_count = 1
                existing.window_started_at = now
            else:
                existing.message_count += 1

            await self._collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"message_count": existing.message_count, "window_started_at": existing.window_started_at}},
            )
            return existing
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to register message for user {user_id} in chat {chat_id}: {exc}") from exc

    async def reset(self, chat_id: int, user_id: int) -> None:
        """Reset a user's flood counter within a chat.

        Args:
            chat_id: The chat to reset.
            user_id: The user whose counter should be reset.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": chat_id, "user_id": user_id},
                {"$set": {"message_count": 0, "window_started_at": datetime.now(timezone.utc)}},
                upsert=True,
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to reset flood counter for user {user_id} in chat {chat_id}: {exc}") from exc
