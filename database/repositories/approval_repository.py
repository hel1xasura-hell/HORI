"""Repository providing data-access methods for approved chat members."""

from __future__ import annotations

from typing import List

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.approval import Approval

logger = get_logger(__name__)


class ApprovalRepository:
    """Encapsulates all read/write operations for the `approvals` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["approvals"]

    async def approve(self, approval: Approval) -> None:
        """Grant a user approval status within a chat.

        Args:
            approval: The `Approval` instance to persist.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"chat_id": approval.chat_id, "user_id": approval.user_id},
                {"$set": approval.to_document()},
                upsert=True,
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to approve user {approval.user_id}: {exc}") from exc

    async def revoke(self, chat_id: int, user_id: int) -> bool:
        """Revoke a user's approval status within a chat.

        Args:
            chat_id: The chat to revoke approval in.
            user_id: The user whose approval should be revoked.

        Returns:
            True if an approval record was deleted, False if none existed.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            result = await self._collection.delete_one({"chat_id": chat_id, "user_id": user_id})
            return result.deleted_count > 0
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to revoke approval for user {user_id}: {exc}") from exc

    async def is_approved(self, chat_id: int, user_id: int) -> bool:
        """Check whether a user is currently approved within a chat.

        Args:
            chat_id: The chat to check.
            user_id: The user to check.

        Returns:
            True if the user has an active approval record.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"chat_id": chat_id, "user_id": user_id})
            return document is not None
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to check approval for user {user_id}: {exc}") from exc

    async def list_for_chat(self, chat_id: int) -> List[Approval]:
        """List all users approved within a chat.

        Args:
            chat_id: The chat to list approvals for.

        Returns:
            A list of `Approval` instances.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            cursor = self._collection.find({"chat_id": chat_id})
            documents = await cursor.to_list(length=None)
            return [Approval.from_document(doc) for doc in documents]
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to list approvals for chat {chat_id}: {exc}") from exc
