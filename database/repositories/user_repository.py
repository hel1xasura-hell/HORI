"""Repository providing data-access methods for globally tracked users."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import RepositoryError
from core.logger import get_logger
from database.models.user import User

logger = get_logger(__name__)


class UserRepository:
    """Encapsulates all read/write operations for the `users` collection."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        """Initialize the repository with a database handle.

        Args:
            database: The active Motor database handle.
        """
        self._collection: AsyncIOMotorCollection = database["users"]

    async def upsert_seen_user(self, user_id: int, username: Optional[str], first_name: str) -> None:
        """Record or refresh a user's basic profile information.

        Args:
            user_id: The Telegram user ID.
            username: The user's current @username, if set.
            first_name: The user's first name.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "username": username,
                        "first_name": first_name,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc), "is_banned_globally": False},
                },
                upsert=True,
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to upsert user {user_id}: {exc}") from exc

    async def find_by_id(self, user_id: int) -> Optional[User]:
        """Find a user by their Telegram ID.

        Args:
            user_id: The Telegram user ID to look up.

        Returns:
            The matching `User`, or None if not found.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one({"user_id": user_id})
            return User.from_document(document) if document else None
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to find user {user_id}: {exc}") from exc

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by their @username, case-insensitively.

        Args:
            username: The username to search for, without the "@" prefix.

        Returns:
            The matching `User`, or None if not found.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            document = await self._collection.find_one(
                {"username": {"$regex": f"^{username}$", "$options": "i"}}
            )
            return User.from_document(document) if document else None
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to find user by username '{username}': {exc}") from exc

    async def set_global_ban(self, user_id: int, banned: bool, reason: Optional[str] = None) -> None:
        """Set or clear a user's global ban status.

        Args:
            user_id: The Telegram user ID.
            banned: Whether the user should be marked as globally banned.
            reason: The reason for the ban, if applicable.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            await self._collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "is_banned_globally": banned,
                        "gban_reason": reason,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
                upsert=True,
            )
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to set global ban for user {user_id}: {exc}") from exc

    async def count_all(self) -> int:
        """Return the total number of users known to the bot.

        Returns:
            The number of documents in the `users` collection.

        Raises:
            RepositoryError: If the underlying database operation fails.
        """
        try:
            return await self._collection.count_documents({})
        except PyMongoError as exc:
            raise RepositoryError(f"Failed to count users: {exc}") from exc
