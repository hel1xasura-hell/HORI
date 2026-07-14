"""General-purpose helper functions that don't fit a more specific module."""

from __future__ import annotations

from typing import Iterable, List, TypeVar

T = TypeVar("T")


def chunk_list(items: List[T], chunk_size: int) -> Iterable[List[T]]:
    """Split a list into consecutive chunks of a given size.

    Args:
        items: The list to split.
        chunk_size: The maximum size of each chunk.

    Yields:
        Successive sub-lists of at most `chunk_size` elements.
    """
    for start_index in range(0, len(items), chunk_size):
        yield items[start_index : start_index + chunk_size]


def safe_int(value: str, default: int = 0) -> int:
    """Convert a string to an integer, returning a default on failure.

    Args:
        value: The string to convert.
        default: The value to return if conversion fails.

    Returns:
        The parsed integer, or `default` if parsing fails.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def deduplicate_preserve_order(items: List[T]) -> List[T]:
    """Remove duplicate items from a list while preserving first-seen order.

    Args:
        items: The list to deduplicate.

    Returns:
        A new list with duplicates removed.
    """
    seen: set = set()
    result: List[T] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def percentage(part: int, whole: int) -> float:
    """Calculate a percentage, safely handling a zero denominator.

    Args:
        part: The numerator value.
        whole: The denominator value.

    Returns:
        The percentage as a float, or 0.0 if `whole` is zero.
    """
    if whole == 0:
        return 0.0
    return round((part / whole) * 100, 2)
