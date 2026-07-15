"""Handlers letting admins connect their private chat to a managed group."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError, PermissionDeniedError
from core.logger import get_logger
from database.mongo import get_mongo_connection
from database.repositories.connection_repository import ConnectionRepository
from utils.chat import get_chat_display_title
from utils.parser import get_command_args
from utils.permissions import is_user_chat_admin

logger = get_logger(__name__)


def _get_repository() -> ConnectionRepository:
    """Build a fresh `ConnectionRepository` bound to the active database.

    Returns:
        A `ConnectionRepository` instance.
    """
    return ConnectionRepository(get_mongo_connection().get_database())


@catch_errors
async def _handle_connect(client: Client, message: Message) -> None:
    """Connect the sender's private chat to a group they administer.

    Usage (in private chat): /connect <chat_id>

    Args:
        client: The active Pyrogram client.
        message: The incoming `/connect` command message.
    """
    if message.chat.type != ChatType.PRIVATE:
        raise InvalidArgumentError("This command can only be used in a private chat with me.")

    args = get_command_args(message)
    if not args or not args[0].lstrip("-").isdigit():
        raise InvalidArgumentError("Usage: /connect <chat_id>")

    target_chat_id = int(args[0])

    if not await is_user_chat_admin(client, target_chat_id, message.from_user.id):
        raise PermissionDeniedError("You must be an administrator of that chat to connect to it.")

    try:
        chat = await client.get_chat(target_chat_id)
    except RPCError as exc:
        raise InvalidArgumentError("I couldn't find that chat. Make sure I'm a member of it.") from exc

    await _get_repository().connect(message.from_user.id, target_chat_id)
    await message.reply_text(f"✅ Connected to <b>{get_chat_display_title(chat)}</b>.")
    logger.info("User_id=%s connected to chat_id=%s", message.from_user.id, target_chat_id)


@catch_errors
async def _handle_disconnect(client: Client, message: Message) -> None:
    """Disconnect the sender's private chat from any connected group.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/disconnect` command message.
    """
    if message.chat.type != ChatType.PRIVATE:
        raise InvalidArgumentError("This command can only be used in a private chat with me.")

    disconnected = await _get_repository().disconnect(message.from_user.id)
    if disconnected:
        await message.reply_text("✅ Disconnected from the connected chat.")
    else:
        await message.reply_text("You are not currently connected to any chat.")


def register(client: Client) -> None:
    """Register all connection handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_connect, filters.command("connect") & filters.private))
    client.add_handler(MessageHandler(_handle_disconnect, filters.command("disconnect") & filters.private))
