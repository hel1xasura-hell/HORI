"""Handlers for small, general-purpose utility commands."""

from __future__ import annotations

import time

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.decorators import catch_errors
from core.logger import get_logger
from database.mongo import get_mongo_connection
from database.repositories.chat_repository import ChatRepository
from database.repositories.user_repository import UserRepository
from utils.users import get_full_name, resolve_target_user

logger = get_logger(__name__)


@catch_errors
async def _handle_ping(client: Client, message: Message) -> None:
    """Measure and report the bot's round-trip response latency.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/ping` command message.
    """
    start_time = time.monotonic()
    reply = await message.reply_text("🏓 Pong!")
    elapsed_ms = (time.monotonic() - start_time) * 1000
    await reply.edit_text(f"🏓 Pong! `{elapsed_ms:.0f}ms`")


@catch_errors
async def _handle_id(client: Client, message: Message) -> None:
    """Report the chat ID, and the sender's or a replied-to user's ID.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/id` command message.
    """
    lines = [f"<b>Chat ID:</b> <code>{message.chat.id}</code>"]

    target = await resolve_target_user(client, message)
    if target:
        lines.append(f"<b>User ID:</b> <code>{target.id}</code> ({get_full_name(target)})")
    elif message.from_user:
        lines.append(f"<b>Your ID:</b> <code>{message.from_user.id}</code>")

    await message.reply_text("\n".join(lines))


@catch_errors
async def _handle_stats(client: Client, message: Message) -> None:
    """Report the number of chats and users the bot is tracking.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/stats` command message.
    """
    database = get_mongo_connection().get_database()
    chat_count = await ChatRepository(database).count_all()
    user_count = await UserRepository(database).count_all()
    await message.reply_text(
        f"📊 <b>Bot statistics</b>\nChats: {chat_count}\nUsers tracked: {user_count}"
    )


@catch_errors
async def _handle_track_user(client: Client, message: Message) -> None:
    """Record the sender's profile information for later username/ID lookup.

    Args:
        client: The active Pyrogram client.
        message: Any incoming message from a user.
    """
    if message.from_user is None or message.from_user.is_bot:
        return

    database = get_mongo_connection().get_database()
    await UserRepository(database).upsert_seen_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name or ""
    )


def register(client: Client) -> None:
    """Register all misc handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_ping, filters.command("ping")))
    client.add_handler(MessageHandler(_handle_id, filters.command("id")))
    client.add_handler(MessageHandler(_handle_stats, filters.command("stats")))
    client.add_handler(MessageHandler(_handle_track_user, filters.incoming), group=1)
