"""Helper functions for checking Telegram chat member permissions."""

from __future__ import annotations

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import RPCError

from config.config import get_config

_ADMIN_STATUSES = (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def is_user_chat_admin(client: Client, chat_id: int, user_id: int) -> bool:
    """Determine whether a user is an administrator or owner of a chat.

    Bot owner and sudo users configured via environment variables are always
    treated as administrators, regardless of their actual chat status.

    Args:
        client: The active Pyrogram client.
        chat_id: The chat to check membership in.
        user_id: The Telegram user ID to check.

    Returns:
        True if the user is a chat admin/owner or a bot-level privileged user.
    """
    if user_id in get_config().privileged_users:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in _ADMIN_STATUSES
    except RPCError:
        return False


async def is_bot_chat_admin(client: Client, chat_id: int) -> bool:
    """Determine whether the bot itself has administrator rights in a chat.

    Args:
        client: The active Pyrogram client.
        chat_id: The chat to check.

    Returns:
        True if the bot is an administrator or owner of the chat.
    """
    try:
        bot_user = await client.get_me()
        member = await client.get_chat_member(chat_id, bot_user.id)
        return member.status in _ADMIN_STATUSES
    except RPCError:
        return False


async def can_bot_restrict_members(client: Client, chat_id: int) -> bool:
    """Determine whether the bot has permission to restrict chat members.

    Args:
        client: The active Pyrogram client.
        chat_id: The chat to check.

    Returns:
        True if the bot is an admin with the `can_restrict_members` privilege.
    """
    try:
        bot_user = await client.get_me()
        member = await client.get_chat_member(chat_id, bot_user.id)
        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return member.status == ChatMemberStatus.OWNER
        privileges = member.privileges
        return bool(privileges and privileges.can_restrict_members)
    except RPCError:
        return False


def is_target_protected(target_user_id: int) -> bool:
    """Determine whether a target user is protected from moderation actions.

    Protected users include the bot owner and any configured sudo users, who
    should never be warnable, mutable, kickable, or bannable by other admins.

    Args:
        target_user_id: The Telegram user ID of the moderation target.

    Returns:
        True if the target is a protected, privileged user.
    """
    return target_user_id in get_config().privileged_users
