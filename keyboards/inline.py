"""Builders for inline keyboards used throughout the bot."""

from __future__ import annotations

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from core.constants import BOT_NAME, SOURCE_URL


def build_start_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    """Build the inline keyboard shown alongside the `/start` message.

    Args:
        bot_username: The bot's own @username, without the "@" prefix.

    Returns:
        An `InlineKeyboardMarkup` with add-to-group, help, and source links.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ Add me to your group",
                    url=f"https://t.me/{bot_username}?startgroup=true",
                )
            ],
            [
                InlineKeyboardButton("📖 Help", callback_data="help:menu"),
                InlineKeyboardButton("🌐 Source", url=SOURCE_URL),
            ],
        ]
    )


def build_help_keyboard() -> InlineKeyboardMarkup:
    """Build the inline keyboard for the `/help` category menu.

    Returns:
        An `InlineKeyboardMarkup` listing each help category as a button.
    """
    categories = [
        ("🛡 Moderation", "help:moderation"),
        ("⚠️ Warnings", "help:warns"),
        ("👋 Welcomes", "help:welcomes"),
        ("🔍 Filters", "help:filters"),
        ("🔒 Locks", "help:locks"),
        ("🚫 Antispam", "help:antispam"),
        ("✅ Approvals", "help:approvals"),
        ("🔗 Connections", "help:connections"),
        ("🏛 Federations", "help:federations"),
    ]
    rows = [
        [InlineKeyboardButton(text, callback_data=data) for text, data in categories[i : i + 2]]
        for i in range(0, len(categories), 2)
    ]
    rows.append([InlineKeyboardButton("« Back", callback_data="help:home")])
    return InlineKeyboardMarkup(rows)


def build_back_keyboard(target: str = "help:home") -> InlineKeyboardMarkup:
    """Build a simple single-button "back" keyboard.

    Args:
        target: The callback data the back button should trigger.

    Returns:
        An `InlineKeyboardMarkup` with a single back button.
    """
    return InlineKeyboardMarkup([[InlineKeyboardButton("« Back", callback_data=target)]])


def build_confirmation_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
    """Build a yes/no confirmation keyboard for destructive actions.

    Args:
        confirm_data: The callback data for the confirm button.
        cancel_data: The callback data for the cancel button.

    Returns:
        An `InlineKeyboardMarkup` with confirm and cancel buttons.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=confirm_data),
                InlineKeyboardButton("❌ Cancel", callback_data=cancel_data),
            ]
        ]
    )


def build_footer_keyboard() -> InlineKeyboardMarkup:
    """Build a small footer keyboard advertising the bot's identity.

    Returns:
        An `InlineKeyboardMarkup` with a single, non-interactive-style label.
    """
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"⚡ Powered by {BOT_NAME}", url=SOURCE_URL)]])
  
