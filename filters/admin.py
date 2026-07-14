"""Pyrogram filter that restricts handlers to group administrators."""

from __future__ import annotations

from pyrogram import Client
from pyrogram.filters import create
from pyrogram.types import Message

from core.logger import get_logger
from utils.permissions import is_user_chat_admin

logger = get_logger(__name__)


async def _admin_filter_func(_, client: Client, message: Message) -> bool:
    """Check whether the message sender is an administrator of the chat.

    Args:
        _: The unused filter instance (Pyrogram passes itself here).
        client: The active Pyrogram client.
        message: The incoming message being filtered.

    Returns:
        True if the sender is a chat admin, creator, or bot privileged user.
    """
    if message.from_user is None or message.chat is None:
        return False
    return await is_user_chat_admin(client, message.chat.id, message.from_user.id)


admin_filter = create(_admin_filter_func, name="AdminFilter")
