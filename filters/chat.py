"""Pyrogram filters that restrict handlers based on chat type."""

from __future__ import annotations

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.filters import create
from pyrogram.types import Message


async def _group_filter_func(_, __: Client, message: Message) -> bool:
    """Check whether a message originated in a group or supergroup.

    Args:
        _: The unused filter instance.
        __: The unused Pyrogram client.
        message: The incoming message being filtered.

    Returns:
        True if the message's chat is a group or supergroup.
    """
    if message.chat is None:
        return False
    return message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)


group_filter = create(_group_filter_func, name="GroupFilter")
