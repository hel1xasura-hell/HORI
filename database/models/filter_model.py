"""Model representing a chat-specific keyword auto-reply filter."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class ChatFilter:
    """Represents a single keyword-triggered auto-reply for a chat.

    Attributes:
        chat_id: The chat this filter belongs to.
        keyword: The trigger keyword or phrase, stored in lowercase.
        reply_text: The text to send when the keyword is matched.
        created_by: The Telegram user ID of the admin who created the filter.
        created_at: When this filter was created.
    """

    chat_id: int
    keyword: str
    reply_text: str
    created_by: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `filters` collection.
        """
        return {
            "chat_id": self.chat_id,
            "keyword": self.keyword.lower(),
            "reply_text": self.reply_text,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "ChatFilter":
        """Deserialize a MongoDB document into a `ChatFilter` instance.

        Args:
            document: A raw dictionary retrieved from the `filters` collection.

        Returns:
            A populated `ChatFilter` instance.
        """
        return cls(
            chat_id=document["chat_id"],
            keyword=document["keyword"],
            reply_text=document["reply_text"],
            created_by=document["created_by"],
            created_at=document.get("created_at", datetime.now(timezone.utc)),
        )
