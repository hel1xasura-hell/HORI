"""Model representing per-user flood/spam tracking within a chat."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class FloodControl:
    """Tracks recent message activity for a user in a chat for antispam purposes.

    Attributes:
        chat_id: The chat being monitored.
        user_id: The Telegram user ID being tracked.
        message_count: Number of messages sent within the current window.
        window_started_at: When the current counting window began.
    """

    chat_id: int
    user_id: int
    message_count: int = 0
    window_started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `flood_control` collection.
        """
        return {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "message_count": self.message_count,
            "window_started_at": self.window_started_at,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "FloodControl":
        """Deserialize a MongoDB document into a `FloodControl` instance.

        Args:
            document: A raw dictionary retrieved from the `flood_control` collection.

        Returns:
            A populated `FloodControl` instance.
        """
        return cls(
            chat_id=document["chat_id"],
            user_id=document["user_id"],
            message_count=document.get("message_count", 0),
            window_started_at=document.get("window_started_at", datetime.now(timezone.utc)),
        )
