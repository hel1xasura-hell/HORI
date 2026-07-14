"""Helper functions for working with dates and times."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime.

    Returns:
        The current UTC datetime.
    """
    return datetime.now(timezone.utc)


def seconds_from_now(seconds: int) -> datetime:
    """Compute a UTC datetime offset a number of seconds into the future.

    Args:
        seconds: The number of seconds to add to the current time.

    Returns:
        The resulting future UTC datetime.
    """
    return utc_now() + timedelta(seconds=seconds)


def format_timestamp(value: datetime, fmt: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Format a datetime as a human-readable UTC string.

    Args:
        value: The datetime to format. Naive datetimes are assumed to be UTC.
        fmt: The strftime-compatible format string.

    Returns:
        The formatted timestamp string.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime(fmt)


def is_expired(expires_at: datetime) -> bool:
    """Determine whether a given expiry timestamp has already passed.

    Args:
        expires_at: The expiry datetime to check. Naive datetimes are
            assumed to be UTC.

    Returns:
        True if the current time is at or past `expires_at`.
    """
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return utc_now() >= expires_at
