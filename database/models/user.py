"""Model representing a globally tracked Telegram user."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class User:
    """Represents a Telegram user known to the bot.

    Attributes:
        user_id: The unique Telegram user identifier.
        username: The user's current @username, without the "@" prefix.
        first_name: The user's first name.
        is_banned_globally: Whether this user is globally banned (gbanned).
        gban_reason: The reason recorded for a global ban, if any.
        created_at: When this user record was first created.
        updated_at: When this user record was last modified.
    """

    user_id: int
    username: str | None = None
    first_name: str = ""
    is_banned_globally: bool = False
    gban_reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `users` collection.
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "is_banned_globally": self.is_banned_globally,
            "gban_reason": self.gban_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "User":
        """Deserialize a MongoDB document into a `User` instance.

        Args:
            document: A raw dictionary retrieved from the `users` collection.

        Returns:
            A populated `User` instance.
        """
        return cls(
            user_id=document["user_id"],
            username=document.get("username"),
            first_name=document.get("first_name", ""),
            is_banned_globally=document.get("is_banned_globally", False),
            gban_reason=document.get("gban_reason"),
            created_at=document.get("created_at", datetime.now(timezone.utc)),
            updated_at=document.get("updated_at", datetime.now(timezone.utc)),
        )
