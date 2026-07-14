"""Helper functions for formatting text sent back to Telegram chats."""

from __future__ import annotations

from html import escape
from typing import Mapping

TEMPLATE_KEYS = ("mention", "first_name", "last_name", "username", "chat_title", "user_id", "chat_id")


def escape_html(text: str) -> str:
    """Escape special HTML characters in a string.

    Args:
        text: The raw text to escape.

    Returns:
        The HTML-safe version of the text.
    """
    return escape(text, quote=False)


def render_template(template: str, values: Mapping[str, str]) -> str:
    """Render a message template, substituting known placeholders safely.

    Unrecognized placeholders are left untouched rather than raising, so a
    malformed template never crashes a handler.

    Args:
        template: The template string containing `{placeholder}` tokens.
        values: A mapping of placeholder names to their replacement values.

    Returns:
        The rendered string with all known placeholders substituted.
    """
    rendered = template
    for key in TEMPLATE_KEYS:
        if key in values:
            rendered = rendered.replace(f"{{{key}}}", values[key])
    return rendered


def format_duration(seconds: int) -> str:
    """Format a duration in seconds as a short human-readable string.

    Args:
        seconds: The duration in seconds.

    Returns:
        A compact string such as "1h 30m" or "45s".
    """
    if seconds < 60:
        return f"{seconds}s"
    minutes, remaining_seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s" if remaining_seconds else f"{minutes}m"
    hours, remaining_minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}h {remaining_minutes}m" if remaining_minutes else f"{hours}h"
    days, remaining_hours = divmod(hours, 24)
    return f"{days}d {remaining_hours}h" if remaining_hours else f"{days}d"


def truncate(text: str, max_length: int = 4096) -> str:
    """Truncate text to fit within Telegram's message length limits.

    Args:
        text: The text to truncate.
        max_length: The maximum allowed length, defaulting to Telegram's cap.

    Returns:
        The original text if within bounds, otherwise a truncated version
        with an ellipsis marker appended.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rstrip() + "…"


def bulleted_list(items: list[str]) -> str:
    """Render a list of strings as a bulleted, newline-separated block.

    Args:
        items: The items to render.

    Returns:
        A string with each item prefixed by "• " on its own line.
    """
    return "\n".join(f"• {item}" for item in items)
