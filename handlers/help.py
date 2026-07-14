"""Handler for the `/help` command and its inline category menu."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.handlers import CallbackQueryHandler, MessageHandler
from pyrogram.types import CallbackQuery, Message

from core.constants import BOT_NAME
from core.decorators import catch_errors
from core.logger import get_logger
from keyboards.inline import build_back_keyboard, build_help_keyboard

logger = get_logger(__name__)

_HOME_TEXT = (
    f"📖 <b>{BOT_NAME} Help</b>\n\n"
    "Choose a category below to see the commands available in that area. "
    "Most moderation commands work by replying to a user's message, or by "
    "passing their @username or user ID as an argument."
)

HELP_CATEGORIES: dict[str, tuple[str, str]] = {
    "moderation": (
        "🛡 Moderation",
        "/mute [reply|user] [reason] — Mute a user\n"
        "/unmute [reply|user] — Unmute a user\n"
        "/kick [reply|user] [reason] — Kick a user\n"
        "/ban [reply|user] [reason] — Ban a user\n"
        "/unban [reply|user] — Unban a user\n"
        "/pin — Pin the replied-to message\n"
        "/unpin — Unpin the replied-to message\n"
        "/purge — Delete messages from the replied-to message to now",
    ),
    "warns": (
        "⚠️ Warnings",
        "/warn [reply|user] [reason] — Warn a user\n"
        "/warns [reply|user] — Show a user's warning count\n"
        "/unwarn [reply|user] — Remove one warning\n"
        "/resetwarns [reply|user] — Clear all warnings\n"
        "/warnlimit <n> — Set the warn limit for this chat",
    ),
    "welcomes": (
        "👋 Welcomes",
        "/welcome on|off — Toggle welcome messages\n"
        "/setwelcome <text> — Set the welcome message template\n"
        "/goodbye on|off — Toggle goodbye messages\n"
        "/setgoodbye <text> — Set the goodbye message template",
    ),
    "filters": (
        "🔍 Filters",
        "/filter <keyword> <reply> — Add a keyword auto-reply\n"
        "/filters — List all filters in this chat\n"
        "/stop <keyword> — Remove a filter",
    ),
    "locks": (
        "🔒 Locks",
        "/lock <type> — Lock a content type (text, media, url, ...)\n"
        "/unlock <type> — Unlock a content type\n"
        "/locks — Show currently locked types",
    ),
    "antispam": (
        "🚫 Antispam",
        "/setflood <n> — Set the flood message threshold\n"
        "/setflood off — Disable flood protection",
    ),
    "approvals": (
        "✅ Approvals",
        "/approve [reply|user] — Exempt a user from locks/antispam\n"
        "/unapprove [reply|user] — Remove a user's approval\n"
        "/approved — List approved users in this chat",
    ),
    "connections": (
        "🔗 Connections",
        "/connect <chat_id> — Manage a group's settings from private chat\n"
        "/disconnect — Disconnect from the currently connected chat",
    ),
    "federations": (
        "🏛 Federations",
        "/newfed <name> — Create a new federation\n"
        "/joinfed <fed_id> — Join this chat to a federation\n"
        "/fban [reply|user] [reason] — Ban a user across the federation\n"
        "/fedinfo — Show information about this chat's federation",
    ),
}


@catch_errors
async def _handle_help_command(client: Client, message: Message) -> None:
    """Reply to the `/help` command with the top-level category menu.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/help` command message.
    """
    await message.reply_text(_HOME_TEXT, reply_markup=build_help_keyboard())


@catch_errors
async def _handle_help_callback(client: Client, callback_query: CallbackQuery) -> None:
    """Handle taps on the help category inline keyboard.

    Args:
        client: The active Pyrogram client.
        callback_query: The incoming callback query, with data like "help:warns".
    """
    _, _, category = callback_query.data.partition(":")

    if category == "menu" or category == "":
        await callback_query.edit_message_text(_HOME_TEXT, reply_markup=build_help_keyboard())
    elif category == "home":
        await callback_query.edit_message_text(_HOME_TEXT, reply_markup=build_help_keyboard())
    elif category in HELP_CATEGORIES:
        title, body = HELP_CATEGORIES[category]
        await callback_query.edit_message_text(
            f"<b>{title}</b>\n\n{body}", reply_markup=build_back_keyboard()
        )
    else:
        await callback_query.answer("Unknown help category.", show_alert=True)
        return

    await callback_query.answer()


def register(client: Client) -> None:
    """Register the `/help` command and callback handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_help_command, filters.command("help")))
    client.add_handler(CallbackQueryHandler(_handle_help_callback, filters.regex(r"^help:")))
