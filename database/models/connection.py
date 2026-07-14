"""Model representing a user's active private-chat connection to a group."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Connection:
    """Represents a user's link between their private chat and a managed group.

    Attributes:
        user_id: The Telegram user ID who owns this connection.
        chat_id: The group chat currently connected to.
    """

    user_id: int
    chat_id: int

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `connections` collection.
        """
        return {"user_id": self.user_id, "chat_id": self.chat_id}

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "Connection":
        """Deserialize a MongoDB document into a `Connection` instance.

        Args:
            document: A raw dictionary retrieved from the `connections` collection.

        Returns:
            A populated `Connection` instance.
        """
        return cls(user_id=document["user_id"], chat_id=document["chat_id"])
  
