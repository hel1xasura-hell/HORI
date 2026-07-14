"""Repository providing data-access methods for welcome/goodbye settings."""

from __future__ import annotations

from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.welcome import Welcome

logger = get_logger(__name__)


class WelcomeRepository:
    """Encapsulates all read/write operations for the `welcomes` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["welcomes"]

    async def get(self, chat_id: int) -> Welcome:
        """Fetch a chat's welcome settings, defaulting to standard values.

        Args:
            chat_id: The chat to fetch settings for.

        Returns:
            The existing or a freshly initialized `Welcome` instance.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"chat_id": chat_id})
            if document is not None:
                return Welcome.from_document(document)
            return Welcome(chat_id=chat_id)
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fetch welcome settings for chat {chat_id}: {exc}") from exc

    async def update(self, chat_id: int, updates: Dict[str, Any]) -> None:
        """Apply a partial update to a chat's welcome settings.

        Args:
            chat_id: The chat to update.
            updates: A mapping of field names to new values.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": chat_id}, {"$set": updates}, upsert=True
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to update welcome settings for chat {chat_id}: {exc}") from exc
