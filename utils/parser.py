"""Helper functions for parsing Telegram command arguments."""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from pyrogram.types import Message

_DURATION_PATTERN = re.compile(r"^(\d+)([smhdw])$", re.IGNORECASE)
_DURATION_MULTIPLIERS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def get_command_args(message: Message) -> List[str]:
    """Return a command message's arguments, excluding the command itself.

    Args:
        message: The command message to parse.

    Returns:
        A list of argument tokens, or an empty list if there are none.
    """
    if not message.command:
        return []
    return message.command[1:]


def parse_duration(text: str) -> Optional[int]:
    """Parse a short duration string (e.g. "10m", "2h", "1d") into seconds.

    Args:
        text: The duration string to parse.

    Returns:
        The duration in seconds, or None if the string is not a valid
        duration expression.
    """
    match = _DURATION_PATTERN.match(text.strip())
    if not match:
        return None
    amount, unit = match.groups()
    return int(amount) * _DURATION_MULTIPLIERS[unit.lower()]


def split_target_and_reason(args: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """Split a command's arguments into a target identifier and a reason.

    The first argument is treated as the target (user ID or @username), and
    any remaining arguments are joined into a free-text reason.

    Args:
        args: The command's argument tokens.

    Returns:
        A tuple of `(target, reason)`, either of which may be None if not
        present in the arguments.
    """
    if not args:
        return None, None
    target = args[0]
    reason = " ".join(args[1:]) if len(args) > 1 else None
    return target, reason


def normalize_keyword(keyword: str) -> str:
    """Normalize a filter keyword for consistent, case-insensitive matching.

    Args:
        keyword: The raw keyword text.

    Returns:
        The lowercased, whitespace-trimmed keyword.
    """
    return keyword.strip().lower()
