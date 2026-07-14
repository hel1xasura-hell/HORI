"""Handler for the `/start` command."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.constants import BOT_NAME, BOT_VERSION
from core.decorators import catch_errors
from core.logger import get_logger
from keyboards.inline import build_start_keyboard

logger = get_logger(__name__)

_START_TEXT_PRIVATE = (
    "👋 <b>Hello! I'm {bot_name}.</b>\n\n"
    "I'm a full-featured group moderation assistant, inspired by the best "
    "admin bots out there. I can handle warnings, welcomes, filters, locks, "
    "antispam, approvals, federations, and more.\n\n"
    "Add me to your group and promote me to admin to get started, or tap "
    "<b>Help</b> below to see everything I can do."
)

_START_TEXT_GROUP = "👋 <b>{bot_name} is online and ready to help moderate this chat!</b>\nUse /help to see available commands."


@catch_errors
async def _handle_start(client: Client, message: Message) -> None:
    """Reply to the `/start` command with an introduction and keyboard.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/start` command message.
    """
    if message.chat.type == ChatType.PRIVATE:
        bot_identity = await client.get_me()
        await message.reply_text(
            _START_TEXT_PRIVATE.format(bot_name=BOT_NAME),
            reply_markup=build_start_keyboard(bot_identity.username or ""),
        )
    else:
        await message.reply_text(_START_TEXT_GROUP.format(bot_name=BOT_NAME))

    logger.debug("Handled /start in chat_id=%s (version=%s)", message.chat.id, BOT_VERSION)


def register(client: Client) -> None:
    """Register the `/start` handler on the given client.

    Args:
        client: The Pyrogram client to attach the handler to.
    """
    client.add_handler(MessageHandler(_handle_start, filters.command("start")))

