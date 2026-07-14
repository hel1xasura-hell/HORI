"""Model representing an approved user exempt from chat locks/restrictions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class Approval:
    """Represents a user approved to bypass locks and antispam in a chat.

    Attributes:
        chat_id: The chat the approval applies to.
        user_id: The approved user's Telegram ID.
        approved_by: The Telegram user ID of the admin who granted approval.
        approved_at: When the approval was granted.
    """

    chat_id: int
    user_id: int
    approved_by: int
    approved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `approvals` collection.
        """
        return {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "Approval":
        """Deserialize a MongoDB document into an `Approval` instance.

        Args:
            document: A raw dictionary retrieved from the `approvals` collection.

        Returns:
            A populated `Approval` instance.
        """
        return cls(
            chat_id=document["chat_id"],
            user_id=document["user_id"],
            approved_by=document["approved_by"],
            approved_at=document.get("approved_at", datetime.now(timezone.utc)),
        )
