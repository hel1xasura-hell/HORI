"""Pyrogram filters that restrict handlers to the bot owner or sudo users."""

from __future__ import annotations

from pyrogram import Client
from pyrogram.filters import create
from pyrogram.types import Message

from config.config import get_config


async def _owner_filter_func(_, __: Client, message: Message) -> bool:
    """Check whether the message sender is the configured bot owner.

    Args:
        _: The unused filter instance.
        __: The unused Pyrogram client.
        message: The incoming message being filtered.

    Returns:
        True if the sender's user ID matches the configured owner ID.
    """
    if message.from_user is None:
        return False
    return message.from_user.id == get_config().owner_id


async def _sudo_filter_func(_, __: Client, message: Message) -> bool:
    """Check whether the message sender is the owner or a sudo user.

    Args:
        _: The unused filter instance.
        __: The unused Pyrogram client.
        message: The incoming message being filtered.

    Returns:
        True if the sender's user ID is in the configured privileged users list.
    """
    if message.from_user is None:
        return False
    return message.from_user.id in get_config().privileged_users


owner_filter = create(_owner_filter_func, name="OwnerFilter")
sudo_filter = create(_sudo_filter_func, name="SudoFilter")
