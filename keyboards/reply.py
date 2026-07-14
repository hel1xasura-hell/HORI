"""Builders for reply keyboards used throughout the bot."""

from __future__ import annotations

from pyrogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def build_confirmation_reply_keyboard() -> ReplyKeyboardMarkup:
    """Build a simple Yes/No reply keyboard for confirmation prompts.

    Returns:
        A `ReplyKeyboardMarkup` with "Yes" and "No" buttons.
    """
    return ReplyKeyboardMarkup(
        [[KeyboardButton("Yes"), KeyboardButton("No")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def remove_reply_keyboard() -> ReplyKeyboardRemove:
    """Build a marker that removes any active reply keyboard from a chat.

    Returns:
        A `ReplyKeyboardRemove` instance.
    """
    return ReplyKeyboardRemove()
