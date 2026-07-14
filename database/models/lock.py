"""Model representing which content types are locked in a chat."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ChatLocks:
    """Represents the set of content/permission locks active in a chat.

    Attributes:
        chat_id: The chat these locks apply to.
        locked_types: The list of `LockableType` values currently locked,
            stored as their string values.
    """

    chat_id: int
    locked_types: List[str] = field(default_factory=list)

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `locks` collection.
        """
        return {"chat_id": self.chat_id, "locked_types": self.locked_types}

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "ChatLocks":
        """Deserialize a MongoDB document into a `ChatLocks` instance.

        Args:
            document: A raw dictionary retrieved from the `locks` collection.

        Returns:
            A populated `ChatLocks` instance.
        """
        return cls(
            chat_id=document["chat_id"],
            locked_types=document.get("locked_types", []),
        )
