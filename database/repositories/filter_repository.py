"""Repository providing data-access methods for chat keyword filters."""

from __future__ import annotations

from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.filter_model import ChatFilter

logger = get_logger(__name__)


class FilterRepository:
    """Encapsulates all read/write operations for the `filters` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["filters"]

    async def add(self, chat_filter: ChatFilter) -> None:
        """Insert or replace a keyword filter for a chat.

        Args:
            chat_filter: The `ChatFilter` instance to persist.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": chat_filter.chat_id, "keyword": chat_filter.keyword.lower()},
                {"$set": chat_filter.to_document()},
                upsert=True,
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to add filter '{chat_filter.keyword}': {exc}") from exc

    async def get(self, chat_id: int, keyword: str) -> Optional[ChatFilter]:
        """Fetch a single filter by chat and keyword.

        Args:
            chat_id: The chat to search within.
            keyword: The keyword to look up.

        Returns:
            The matching `ChatFilter`, or None if not found.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"chat_id": chat_id, "keyword": keyword.lower()})
            return ChatFilter.from_document(document) if document else None
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to fetch filter '{keyword}': {exc}") from exc

    async def list_for_chat(self, chat_id: int) -> List[ChatFilter]:
        """List all filters configured for a chat.

        Args:
            chat_id: The chat to list filters for.

        Returns:
            A list of `ChatFilter` instances, sorted alphabetically by keyword.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            cursor = self._collection.find({"chat_id": chat_id}).sort("keyword", 1)
            documents = await cursor.to_list(length=None)
            return [ChatFilter.from_document(doc) for doc in documents]
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to list filters for chat {chat_id}: {exc}") from exc

    async def remove(self, chat_id: int, keyword: str) -> bool:
        """Remove a filter by chat and keyword.

        Args:
            chat_id: The chat to remove the filter from.
            keyword: The keyword identifying the filter to remove.

        Returns:
            True if a filter was deleted, False if none matched.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            result = await self._collection.delete_one({"chat_id": chat_id, "keyword": keyword.lower()})
            return result.deleted_count > 0
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to remove filter '{keyword}': {exc}") from exc

    async def remove_all_for_chat(self, chat_id: int) -> int:
        """Remove all filters configured for a chat.

        Args:
            chat_id: The chat whose filters should be removed.

        Returns:
            The number of filters deleted.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            result = await self._collection.delete_many({"chat_id": chat_id})
            return result.deleted_count
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to remove all filters for chat {chat_id}: {exc}") from exc
