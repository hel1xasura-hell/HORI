"""Handlers for managing and triggering chat keyword filters."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError
from core.logger import get_logger
from database.models.filter_model import ChatFilter
from database.mongo import get_mongo_connection
from database.repositories.filter_repository import FilterRepository
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.formatting import bulleted_list
from utils.parser import get_command_args, normalize_keyword

logger = get_logger(__name__)


def _get_repository() -> FilterRepository:
    """Build a fresh `FilterRepository` bound to the active database.

    Returns:
        A `FilterRepository` instance.
    """
    return FilterRepository(get_mongo_connection().get_database())


@catch_errors
async def _handle_add_filter(client: Client, message: Message) -> None:
    """Add a new keyword auto-reply filter to the chat.

    Usage: /filter <keyword> <reply text>

    Args:
        client: The active Pyrogram client.
        message: The incoming `/filter` command message.
    """
    args = get_command_args(message)
    if len(args) < 2:
        raise InvalidArgumentError("Usage: /filter <keyword> <reply text>")

    keyword = normalize_keyword(args[0])
    reply_text = " ".join(args[1:])

    chat_filter = ChatFilter(
        chat_id=message.chat.id,
        keyword=keyword,
        reply_text=reply_text,
        created_by=message.from_user.id,
    )
    await _get_repository().add(chat_filter)
    await message.reply_text(f"✅ Filter added for keyword: <code>{keyword}</code>")
    logger.info("Filter '%s' added in chat_id=%s", keyword, message.chat.id)


@catch_errors
async def _handle_list_filters(client: Client, message: Message) -> None:
    """List all keyword filters configured for this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/filters` command message.
    """
    chat_filters = await _get_repository().list_for_chat(message.chat.id)
    if not chat_filters:
        await message.reply_text("No filters have been set in this chat.")
        return

    keywords = [chat_filter.keyword for chat_filter in chat_filters]
    await message.reply_text(f"📋 <b>Filters in this chat:</b>\n{bulleted_list(keywords)}")


@catch_errors
async def _handle_remove_filter(client: Client, message: Message) -> None:
    """Remove a keyword filter from this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/stop` command message.
    """
    args = get_command_args(message)
    if not args:
        raise InvalidArgumentError("Usage: /stop <keyword>")

    keyword = normalize_keyword(args[0])
    removed = await _get_repository().remove(message.chat.id, keyword)
    if removed:
        await message.reply_text(f"✅ Filter removed: <code>{keyword}</code>")
    else:
        await message.reply_text(f"No filter found for: <code>{keyword}</code>")


@catch_errors
async def _handle_potential_trigger(client: Client, message: Message) -> None:
    """Check an incoming text message against configured filters and reply if matched.

    Args:
        client: The active Pyrogram client.
        message: The incoming text message.
    """
    if not message.text:
        return

    chat_filters = await _get_repository().list_for_chat(message.chat.id)
    if not chat_filters:
        return

    normalized_text = message.text.lower()
    for chat_filter in chat_filters:
        if chat_filter.keyword in normalized_text:
            await message.reply_text(chat_filter.reply_text)
            return


def register(client: Client) -> None:
    """Register all filter handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_add_filter, filters.command("filter") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_list_filters, filters.command("filters") & group_filter))
    client.add_handler(MessageHandler(_handle_remove_filter, filters.command("stop") & group_filter & admin_filter))
    client.add_handler(
        MessageHandler(_handle_potential_trigger, group_filter & filters.text & filters.incoming & ~filters.via_bot)
    )
