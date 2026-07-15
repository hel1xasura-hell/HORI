"""Handlers for welcome/goodbye configuration and member join/leave events."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.handlers import ChatMemberUpdatedHandler, MessageHandler
from pyrogram.types import ChatMemberUpdated, Message

from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError
from core.logger import get_logger
from database.mongo import get_mongo_connection
from database.repositories.welcome_repository import WelcomeRepository
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.chat import get_chat_display_title
from utils.formatting import render_template
from utils.parser import get_command_args
from utils.users import get_full_name, get_user_mention

logger = get_logger(__name__)


def _get_repository() -> WelcomeRepository:
    """Build a fresh `WelcomeRepository` bound to the active database.

    Returns:
        A `WelcomeRepository` instance.
    """
    return WelcomeRepository(get_mongo_connection().get_database())


@catch_errors
async def _handle_member_joined(client: Client, update: ChatMemberUpdated) -> None:
    """Send a welcome message when a new member joins the chat.

    Args:
        client: The active Pyrogram client.
        update: The chat member update event.
    """
    old_status = update.old_chat_member.status if update.old_chat_member else None
    new_status = update.new_chat_member.status if update.new_chat_member else None
    if old_status is not None or new_status is None:
        return

    new_member = update.new_chat_member.user
    if new_member.is_bot:
        return

    settings = await _get_repository().get(update.chat.id)
    if not settings.welcome_enabled:
        return

    values = {
        "mention": get_user_mention(new_member),
        "first_name": new_member.first_name or "",
        "last_name": new_member.last_name or "",
        "username": f"@{new_member.username}" if new_member.username else get_full_name(new_member),
        "chat_title": get_chat_display_title(update.chat),
        "user_id": str(new_member.id),
        "chat_id": str(update.chat.id),
    }
    text = render_template(settings.welcome_text, values)
    await client.send_message(update.chat.id, text)
    logger.debug("Sent welcome message for user_id=%s in chat_id=%s", new_member.id, update.chat.id)


@catch_errors
async def _handle_member_left(client: Client, update: ChatMemberUpdated) -> None:
    """Send a goodbye message when a member leaves the chat.

    Args:
        client: The active Pyrogram client.
        update: The chat member update event.
    """
    new_status = update.new_chat_member.status if update.new_chat_member else None
    if new_status not in ("left", "kicked", "banned"):
        return

    departed_member = update.old_chat_member.user if update.old_chat_member else None
    if departed_member is None or departed_member.is_bot:
        return

    settings = await _get_repository().get(update.chat.id)
    if not settings.goodbye_enabled:
        return

    values = {
        "mention": get_user_mention(departed_member),
        "first_name": departed_member.first_name or "",
        "last_name": departed_member.last_name or "",
        "username": f"@{departed_member.username}" if departed_member.username else get_full_name(departed_member),
        "chat_title": get_chat_display_title(update.chat),
        "user_id": str(departed_member.id),
        "chat_id": str(update.chat.id),
    }
    text = render_template(settings.goodbye_text, values)
    await client.send_message(update.chat.id, text)


@catch_errors
async def _handle_welcome_toggle(client: Client, message: Message) -> None:
    """Enable or disable welcome messages for this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/welcome` command message.
    """
    args = get_command_args(message)
    if not args or args[0].lower() not in ("on", "off"):
        raise InvalidArgumentError("Usage: /welcome on|off")

    enabled = args[0].lower() == "on"
    await _get_repository().update(message.chat.id, {"welcome_enabled": enabled})
    await message.reply_text(f"✅ Welcome messages {'enabled' if enabled else 'disabled'}.")


@catch_errors
async def _handle_set_welcome(client: Client, message: Message) -> None:
    """Set the welcome message template for this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/setwelcome` command message.
    """
    args = get_command_args(message)
    if not args:
        raise InvalidArgumentError(
            "Usage: /setwelcome <text>\nPlaceholders: {mention} {first_name} {username} {chat_title}"
        )

    welcome_text = " ".join(args)
    await _get_repository().update(message.chat.id, {"welcome_text": welcome_text})
    await message.reply_text("✅ Welcome message updated.")


@catch_errors
async def _handle_goodbye_toggle(client: Client, message: Message) -> None:
    """Enable or disable goodbye messages for this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/goodbye` command message.
    """
    args = get_command_args(message)
    if not args or args[0].lower() not in ("on", "off"):
        raise InvalidArgumentError("Usage: /goodbye on|off")

    enabled = args[0].lower() == "on"
    await _get_repository().update(message.chat.id, {"goodbye_enabled": enabled})
    await message.reply_text(f"✅ Goodbye messages {'enabled' if enabled else 'disabled'}.")


@catch_errors
async def _handle_set_goodbye(client: Client, message: Message) -> None:
    """Set the goodbye message template for this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/setgoodbye` command message.
    """
    args = get_command_args(message)
    if not args:
        raise InvalidArgumentError(
            "Usage: /setgoodbye <text>\nPlaceholders: {mention} {first_name} {username} {chat_title}"
        )

    goodbye_text = " ".join(args)
    await _get_repository().update(message.chat.id, {"goodbye_text": goodbye_text})
    await message.reply_text("✅ Goodbye message updated.")


def register(client: Client) -> None:
    """Register all welcome/goodbye handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(ChatMemberUpdatedHandler(_handle_member_joined))
    client.add_handler(ChatMemberUpdatedHandler(_handle_member_left))
    client.add_handler(
        MessageHandler(_handle_welcome_toggle, filters.command("welcome") & group_filter & admin_filter)
    )
    client.add_handler(
        MessageHandler(_handle_set_welcome, filters.command("setwelcome") & group_filter & admin_filter)
    )
    client.add_handler(
        MessageHandler(_handle_goodbye_toggle, filters.command("goodbye") & group_filter & admin_filter)
    )
    client.add_handler(
        MessageHandler(_handle_set_goodbye, filters.command("setgoodbye") & group_filter & admin_filter)
    )
