"""Helper functions for working with Telegram chats."""

from __future__ import annotations

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import Chat


def is_group_chat(chat: Chat) -> bool:
    """Determine whether a chat is a group or supergroup.

    Args:
        chat: The Pyrogram `Chat` object to check.

    Returns:
        True if the chat type is GROUP or SUPERGROUP.
    """
    return chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)


def get_chat_display_title(chat: Chat) -> str:
    """Return a human-readable title for a chat, falling back gracefully.

    Args:
        chat: The Pyrogram `Chat` object.

    Returns:
        The chat's title, or its first/last name if it is a private chat,
        or a generic fallback if no name information is available.
    """
    if chat.title:
        return chat.title
    name_parts = [part for part in (chat.first_name, chat.last_name) if part]
    if name_parts:
        return " ".join(name_parts)
    return f"Chat {chat.id}"


async def get_chat_member_count(client: Client, chat_id: int) -> int:
    """Fetch the number of members in a chat.

    Args:
        client: The active Pyrogram client.
        chat_id: The Telegram chat ID.

    Returns:
        The number of members in the chat, or 0 if it cannot be determined.
    """
    try:
        return await client.get_chat_members_count(chat_id)
    except Exception:  # noqa: BLE001 - member count is best-effort
        return 0
  
