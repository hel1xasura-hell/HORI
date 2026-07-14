"""Model representing a Telegram chat's persisted settings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict

from core.constants import DEFAULT_WARN_ACTION, DEFAULT_WARN_LIMIT, MAX_FLOOD_MESSAGES


@dataclass
class Chat:
    """Represents a Telegram group chat and its moderation settings.

    Attributes:
        chat_id: The unique Telegram chat identifier.
        title: The chat's display title.
        warn_limit: Number of warnings before an automatic action is taken.
        warn_action: The action to take once the warn limit is reached.
        antispam_enabled: Whether flood/antispam protection is active.
        federation_id: The federation this chat is linked to, if any.
        created_at: When this chat record was first created.
        updated_at: When this chat record was last modified.
    """

    chat_id: int
    title: str = ""
    warn_limit: int = DEFAULT_WARN_LIMIT
    warn_action: str = DEFAULT_WARN_ACTION
    antispam_enabled: bool = True
    flood_limit: int = MAX_FLOOD_MESSAGES
    federation_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `chats` collection.
        """
        return {
            "chat_id": self.chat_id,
            "title": self.title,
            "warn_limit": self.warn_limit,
            "warn_action": self.warn_action,
            "antispam_enabled": self.antispam_enabled,
            "flood_limit": self.flood_limit,
            "federation_id": self.federation_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "Chat":
        """Deserialize a MongoDB document into a `Chat` instance.

        Args:
            document: A raw dictionary retrieved from the `chats` collection.

        Returns:
            A populated `Chat` instance.
        """
        return cls(
            chat_id=document["chat_id"],
            title=document.get("title", ""),
            warn_limit=document.get("warn_limit", DEFAULT_WARN_LIMIT),
            warn_action=document.get("warn_action", DEFAULT_WARN_ACTION),
            antispam_enabled=document.get("antispam_enabled", True),
            flood_limit=document.get("flood_limit", MAX_FLOOD_MESSAGES),
            federation_id=document.get("federation_id"),
            created_at=document.get("created_at", datetime.now(timezone.utc)),
            updated_at=document.get("updated_at", datetime.now(timezone.utc)),
        )
