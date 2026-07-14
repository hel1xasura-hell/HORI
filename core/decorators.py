"""Reusable decorators for Pyrogram message and callback handlers."""

from __future__ import annotations

import functools
import time
from typing import Any, Awaitable, Callable, TypeVar

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, Message

from core.exceptions import HoriError
from core.logger import get_logger

logger = get_logger(__name__)

HandlerFunc = TypeVar("HandlerFunc", bound=Callable[..., Awaitable[Any]])


def catch_errors(func: HandlerFunc) -> HandlerFunc:
    """Wrap a handler so unexpected exceptions are logged instead of crashing the bot.

    Telegram-level errors (`RPCError`) and domain errors (`HoriError`) are logged
    at WARNING level since they are typically expected/recoverable. Any other
    exception is logged at ERROR level with a full stack trace.

    Args:
        func: The async handler function to wrap. Its first two positional
            arguments are expected to be a `Client` and a `Message` or
            `CallbackQuery`.

    Returns:
        The wrapped handler function.
    """

    @functools.wraps(func)
    async def wrapper(client: Client, update: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return await func(client, update, *args, **kwargs)
        except HoriError as exc:
            logger.warning("Handled domain error in '%s': %s", func.__name__, exc)
            await _notify_user(update, f"⚠️ {exc}")
        except RPCError as exc:
            logger.warning("Telegram API error in '%s': %s", func.__name__, exc)
            await _notify_user(update, "⚠️ A Telegram API error occurred. Please try again.")
        except Exception:  # noqa: BLE001 - top-level safety net by design
            logger.exception("Unexpected error in handler '%s'", func.__name__)
            await _notify_user(update, "❌ An unexpected error occurred. The incident has been logged.")

    return wrapper  # type: ignore[return-value]


async def _notify_user(update: Any, text: str) -> None:
    """Best-effort attempt to inform the user that their action failed.

    Silently does nothing for update types that have no way to reply
    (e.g. `ChatMemberUpdated` events triggered by join/leave handlers).

    Args:
        update: The update object that triggered the failing handler.
        text: The message to show the user.
    """
    try:
        if isinstance(update, CallbackQuery):
            await update.answer(text, show_alert=True)
        elif isinstance(update, Message):
            await update.reply_text(text)
    except RPCError:
        logger.debug("Failed to notify user about handler error; suppressing secondary failure.")


def measure_execution_time(func: HandlerFunc) -> HandlerFunc:
    """Log how long a handler took to execute, useful for spotting slow commands.

    Args:
        func: The async handler function to time.

    Returns:
        The wrapped handler function.
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.monotonic()
        result = await func(*args, **kwargs)
        elapsed_ms = (time.monotonic() - start_time) * 1000
        logger.debug("Handler '%s' completed in %.2fms", func.__name__, elapsed_ms)
        return result

    return wrapper  # type: ignore[return-value]
