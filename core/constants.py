"""Application-wide constant values shared across modules."""

from __future__ import annotations

from enum import Enum

BOT_NAME = "Hori"
BOT_VERSION = "1.0.0"
SOURCE_URL = "https://github.com/your-username/hori"

DEFAULT_WARN_LIMIT = 3
DEFAULT_WARN_ACTION = "mute"
MAX_FLOOD_MESSAGES = 10
MAX_FLOOD_WINDOW_SECONDS = 10

CALLBACK_SEPARATOR = ":"
COMMAND_PREFIXES = ("/", "!")

PAGE_SIZE_DEFAULT = 10


class WarnAction(str, Enum):
    """Actions that may be taken automatically once a user's warn limit is reached."""

    MUTE = "mute"
    KICK = "kick"
    BAN = "ban"
    NONE = "none"


class LockableType(str, Enum):
    """Content or permission types that can be locked in a chat."""

    TEXT = "text"
    MEDIA = "media"
    STICKER = "sticker"
    GIF = "gif"
    URL = "url"
    FORWARD = "forward"
    POLL = "poll"
    GAME = "game"
    LOCATION = "location"
    CONTACT = "contact"
    COMMANDS = "commands"
    INLINE = "inline"
    BOTS = "bots"


class ApprovalStatus(str, Enum):
    """Status values for chat member approvals."""

    APPROVED = "approved"
    REVOKED = "revoked"


class FederationRole(str, Enum):
    """Roles a user may hold within a federation."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
  
