"""Handlers for creating and managing federations, and cross-chat fbans."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError, PermissionDeniedError, TargetUserNotFoundError
from core.logger import get_logger
from database.models.federation import Federation
from database.mongo import get_mongo_connection
from database.repositories.federation_repository import FederationRepository
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.parser import get_command_args
from utils.permissions import is_target_protected
from utils.users import extract_reason, get_user_mention, resolve_target_user

logger = get_logger(__name__)


def _get_repository() -> FederationRepository:
    """Build a fresh `FederationRepository` bound to the active database.

    Returns:
        A `FederationRepository` instance.
    """
    return FederationRepository(get_mongo_connection().get_database())


@catch_errors
async def _handle_new_federation(client: Client, message: Message) -> None:
    """Create a new federation owned by the command sender.

    Usage: /newfed <name>

    Args:
        client: The active Pyrogram client.
        message: The incoming `/newfed` command message.
    """
    args = get_command_args(message)
    if not args:
        raise InvalidArgumentError("Usage: /newfed <name>")

    federation = Federation(name=" ".join(args), owner_id=message.from_user.id)
    await _get_repository().create(federation)
    await message.reply_text(
        f"🏛 Federation <b>{federation.name}</b> created.\n"
        f"Federation ID: <code>{federation.federation_id}</code>\n"
        f"Use /joinfed {federation.federation_id} in a group to link it."
    )
    logger.info("Federation '%s' (%s) created by user_id=%s", federation.name, federation.federation_id, message.from_user.id)


@catch_errors
async def _handle_join_federation(client: Client, message: Message) -> None:
    """Link this chat to an existing federation.

    Usage: /joinfed <federation_id>

    Args:
        client: The active Pyrogram client.
        message: The incoming `/joinfed` command message.
    """
    args = get_command_args(message)
    if not args:
        raise InvalidArgumentError("Usage: /joinfed <federation_id>")

    repository = _get_repository()
    federation = await repository.get_by_id(args[0])
    if federation is None:
        raise InvalidArgumentError("No federation found with that ID.")

    await repository.add_chat(federation.federation_id, message.chat.id)
    await message.reply_text(f"✅ This chat has joined federation <b>{federation.name}</b>.")


@catch_errors
async def _handle_fban(client: Client, message: Message) -> None:
    """Ban a user across every chat in this chat's federation.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/fban` command message.
    """
    repository = _get_repository()
    federation = await repository.get_by_chat(message.chat.id)
    if federation is None:
        raise InvalidArgumentError("This chat is not part of any federation. Use /joinfed first.")

    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")
    if is_target_protected(target.id):
        raise PermissionDeniedError("This user is protected and cannot be fbanned.")

    reason = extract_reason(message, offset=1) or "No reason given"
    await repository.ban_user(federation.federation_id, target.id)

    banned_chats = 0
    for chat_id in federation.chat_ids:
        try:
            await client.ban_chat_member(chat_id, target.id)
            banned_chats += 1
        except RPCError:
            logger.debug("Failed to fban user_id=%s in chat_id=%s; skipping.", target.id, chat_id)

    await message.reply_text(
        f"🔨 {get_user_mention(target)} has been federation-banned in {banned_chats} chat(s).\n"
        f"<b>Reason:</b> {reason}"
    )
    logger.info(
        "Fbanned user_id=%s across federation=%s (%d chats)",
        target.id,
        federation.federation_id,
        banned_chats,
    )


@catch_errors
async def _handle_fedinfo(client: Client, message: Message) -> None:
    """Show information about the federation this chat belongs to.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/fedinfo` command message.
    """
    federation = await _get_repository().get_by_chat(message.chat.id)
    if federation is None:
        await message.reply_text("This chat is not part of any federation.")
        return

    await message.reply_text(
        f"🏛 <b>{federation.name}</b>\n"
        f"ID: <code>{federation.federation_id}</code>\n"
        f"Chats: {len(federation.chat_ids)}\n"
        f"Banned users: {len(federation.banned_user_ids)}"
    )


def register(client: Client) -> None:
    """Register all federation handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_new_federation, filters.command("newfed")))
    client.add_handler(
        MessageHandler(_handle_join_federation, filters.command("joinfed") & group_filter & admin_filter)
    )
    client.add_handler(MessageHandler(_handle_fban, filters.command("fban") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_fedinfo, filters.command("fedinfo") & group_filter))
