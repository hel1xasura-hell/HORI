"""Model representing a chat's welcome/goodbye message configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

DEFAULT_WELCOME_TEXT = "Hey {mention}, welcome to {chat_title}! 👋"
DEFAULT_GOODBYE_TEXT = "{first_name} has left the chat. 👋"


@dataclass
class Welcome:
    """Represents the welcome/goodbye message settings for a chat.

    Attributes:
        chat_id: The chat these settings apply to.
        welcome_enabled: Whether new-member welcome messages are sent.
        welcome_text: The welcome message template, supporting placeholders
            such as `{mention}`, `{first_name}`, and `{chat_title}`.
        goodbye_enabled: Whether member-left goodbye messages are sent.
        goodbye_text: The goodbye message template.
        clean_service_messages: Whether Telegram's own join/leave service
            messages should be deleted automatically.
    """

    chat_id: int
    welcome_enabled: bool = True
    welcome_text: str = DEFAULT_WELCOME_TEXT
    goodbye_enabled: bool = False
    goodbye_text: str = DEFAULT_GOODBYE_TEXT
    clean_service_messages: bool = False

    def to_document(self) -> Dict[str, Any]:
        """Serialize this model into a MongoDB-compatible dictionary.

        Returns:
            A dictionary suitable for insertion into the `welcomes` collection.
        """
        return {
            "chat_id": self.chat_id,
            "welcome_enabled": self.welcome_enabled,
            "welcome_text": self.welcome_text,
            "goodbye_enabled": self.goodbye_enabled,
            "goodbye_text": self.goodbye_text,
            "clean_service_messages": self.clean_service_messages,
        }

    @classmethod
    def from_document(cls, document: Dict[str, Any]) -> "Welcome":
        """Deserialize a MongoDB document into a `Welcome` instance.

        Args:
            document: A raw dictionary retrieved from the `welcomes` collection.

        Returns:
            A populated `Welcome` instance.
        """
        return cls(
            chat_id=document["chat_id"],
            welcome_enabled=document.get("welcome_enabled", True),
            welcome_text=document.get("welcome_text", DEFAULT_WELCOME_TEXT),
            goodbye_enabled=document.get("goodbye_enabled", False),
            goodbye_text=document.get("goodbye_text", DEFAULT_GOODBYE_TEXT),
            clean_service_messages=document.get("clean_service_messages", False),
        )
