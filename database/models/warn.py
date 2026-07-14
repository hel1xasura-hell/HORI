"""Model representing a user's warning record within a single chat."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class Warn:
    """Represents the accumulated warnings for one user in one chat.

    Attributes:
        chat_id: The chat in which the warnings were issued.
        user_id: The warned user's Telegram ID.
        count: The current number of active warnings.
        reasons: The recorded reason for each warning, in issue order.
        updated_at: When this warn record was last modified.
    """

    chat_id: int
    user_id: int
    count: int = 0
    reasons: List[str] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `warns` collection.
        """
        return {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "count": self.count,
            "reasons": self.reasons,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "Warn":
        """Deserialize a MongoDB document into a `Warn` instance.

        Args:
            document: A raw dictionary retrieved from the `warns` collection.

        Returns:
            A populated `Warn` instance.
        """
        return cls(
            chat_id=document["chat_id"],
            user_id=document["user_id"],
            count=document.get("count", 0),
            reasons=document.get("reasons", []),
            updated_at=document.get("updated_at", datetime.now(timezone.utc)),
        )
