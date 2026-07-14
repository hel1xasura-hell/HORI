"""Model representing a federation of chats sharing a common ban list."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4


@dataclass
class Federation:
    """Represents a federation: a group of chats sharing bans and admins.

    Attributes:
        federation_id: A unique identifier for the federation.
        name: The federation's display name.
        owner_id: The Telegram user ID of the federation's owner.
        admin_ids: Telegram user IDs granted federation-admin privileges.
        chat_ids: The chat IDs currently subscribed to this federation.
        banned_user_ids: Telegram user IDs banned across the federation.
        created_at: When the federation was created.
    """

    name: str
    owner_id: int
    federation_id: str = field(default_factory=lambda: uuid4().hex[:12])
    admin_ids: List[int] = field(default_factory=list)
    chat_ids: List[int] = field(default_factory=list)
    banned_user_ids: List[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `federations` collection.
        """
        return {
            "federation_id": self.federation_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "admin_ids": self.admin_ids,
            "chat_ids": self.chat_ids,
            "banned_user_ids": self.banned_user_ids,
            "created_at": self.created_at,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "Federation":
        """Deserialize a MongoDB document into a `Federation` instance.

        Args:
            document: A raw dictionary retrieved from the `federations` collection.

        Returns:
            A populated `Federation` instance.
        """
        return cls(
            federation_id=document["federation_id"],
            name=document["name"],
            owner_id=document["owner_id"],
            admin_ids=document.get("admin_ids", []),
            chat_ids=document.get("chat_ids", []),
            banned_user_ids=document.get("banned_user_ids", []),
            created_at=document.get("created_at", datetime.now(timezone.utc)),
        )
