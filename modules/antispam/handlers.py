"""Handlers for configuring and enforcing flood-based antispam protection."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions, Message

from core.constants import MAX_FLOOD_WINDOW_SECONDS
from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError
from core.logger import get_logger
from database.mongo import get_mongo_connection
from database.repositories.chat_repository import ChatRepository
from database.repositories.flood_repository import FloodRepository
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.parser import get_command_args
from utils.permissions import is_user_chat_admin
from utils.users import get_user_mention

logger = get_logger(__name__)

_FULL_MUTE_PERMISSIONS = ChatPermissions(can_send_messages=False)


def _get_repositories() -> tuple[ChatRepository, FloodRepository]:
    """Build fresh repository instances bound to the active database.

    Returns:
        A tuple of `(ChatRepository, FloodRepository)`.
    """
    database = get_mongo_connection().get_database()
    return ChatRepository(database), FloodRepository(database)


@catch_errors
async def _handle_set_flood(client: Client, message: Message) -> None:
    """Configure this chat's flood message threshold, or disable antispam.

    Usage: /setflood <n> | /setflood off

    Args:
        client: The active Pyrogram client.
        message: The incoming `/setflood` command message.
    """
    args = get_command_args(message)
    if not args:
        raise InvalidArgumentError("Usage: /setflood <number> or /setflood off")

    chat_repo, _ = _get_repositories()

    if args[0].lower() == "off":
        await chat_repo.update_settings(message.chat.id, {"antispam_enabled": False})
        await message.reply_text("✅ Antispam protection disabled.")
        return

    if not args[0].isdigit() or int(args[0]) < 2:
        raise InvalidArgumentError("Flood threshold must be a number of at least 2.")

    flood_limit = int(args[0])
    await chat_repo.update_settings(
        message.chat.id, {"antispam_enabled": True, "flood_limit": flood_limit}
    )
    await message.reply_text(f"✅ Antispam enabled: users will be muted after {flood_limit} messages in {MAX_FLOOD_WINDOW_SECONDS}s.")


@catch_errors
async def _handle_flood_check(client: Client, message: Message) -> None:
    """Track message frequency per user and mute them if they exceed the flood limit.

    Args:
        client: The active Pyrogram client.
        message: The incoming message to evaluate for flood behavior.
    """
    if message.from_user is None:
        return

    if await is_user_chat_admin(client, message.chat.id, message.from_user.id):
        return

    chat_repo, flood_repo = _get_repositories()
    chat_settings = await chat_repo.get_or_create(message.chat.id, message.chat.title or "")

    if not chat_settings.antispam_enabled:
        return

    record = await flood_repo.register_message(
        message.chat.id, message.from_user.id, MAX_FLOOD_WINDOW_SECONDS
    )

    if record.message_count < chat_settings.flood_limit:
        return

    try:
        await client.restrict_chat_member(message.chat.id, message.from_user.id, _FULL_MUTE_PERMISSIONS)
        await message.reply_text(
            f"🚫 {get_user_mention(message.from_user)} was muted for flooding the chat."
        )
    except RPCError:
        logger.debug("Failed to mute flooding user; likely insufficient permissions.")
    finally:
        await flood_repo.reset(message.chat.id, message.from_user.id)


def register(client: Client) -> None:
    """Register all antispam handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(
        MessageHandler(_handle_set_flood, filters.command("setflood") & group_filter & admin_filter)
    )
    client.add_handler(MessageHandler(_handle_flood_check, group_filter & filters.incoming))

