"""Helper functions for resolving and describing Telegram users."""

from __future__ import annotations

from typing import Optional

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import Message, User

from core.exceptions import TargetUserNotFoundError


async def resolve_target_user(client: Client, message: Message) -> Optional[User]:
    """Resolve the user targeted by a moderation command.

    Resolution order:
        1. The user being replied to, if any.
        2. A user ID or @username passed as the first command argument.

    Args:
        client: The active Pyrogram client.
        message: The command message to resolve a target from.

    Returns:
        The resolved `User`, or None if no target could be determined.

    Raises:
        TargetUserNotFoundError: If an explicit argument was given but no
            matching user could be found.
    """
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    if not message.command or len(message.command) < 2:
        return None

    identifier = message.command[1]
    try:
        if identifier.lstrip("-").isdigit():
            fetched_user = await client.get_users(int(identifier))
        else:
            fetched_user = await client.get_users(identifier.lstrip("@"))
        return fetched_user if isinstance(fetched_user, User) else None
    except RPCError as exc:
        raise TargetUserNotFoundError(f"Could not find a user matching '{identifier}'.") from exc


def get_user_mention(user: User) -> str:
    """Build an HTML mention link for a user.

    Args:
        user: The `User` to build a mention for.

    Returns:
        An HTML anchor tag mentioning the user by their first name.
    """
    display_name = user.first_name or user.username or str(user.id)
    return f'<a href="tg://user?id={user.id}">{display_name}</a>'


def get_full_name(user: User) -> str:
    """Combine a user's first and last name into a single display string.

    Args:
        user: The `User` whose name should be formatted.

    Returns:
        The user's full name, falling back to their username or ID.
    """
    parts = [part for part in (user.first_name, user.last_name) if part]
    if parts:
        return " ".join(parts)
    return user.username or str(user.id)


def extract_reason(message: Message, offset: int = 2) -> Optional[str]:
    """Extract a free-text reason from a command's remaining arguments.

    Args:
        message: The command message.
        offset: The number of leading command tokens to skip (typically the
            command itself plus a target argument).

    Returns:
        The joined remaining arguments as a reason string, or None if empty.
    """
    if not message.command or len(message.command) <= offset:
        return None
    return " ".join(message.command[offset:]) or None
