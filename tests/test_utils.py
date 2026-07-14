"""Unit tests for pure utility functions that don't require Telegram or MongoDB."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from utils.formatting import bulleted_list, format_duration, render_template, truncate
from utils.helpers import chunk_list, deduplicate_preserve_order, percentage, safe_int
from utils.parser import normalize_keyword, parse_duration, split_target_and_reason
from utils.time import is_expired, seconds_from_now


class TestFormatting:
    """Tests for text formatting helpers."""

    def test_render_template_substitutes_known_placeholders(self) -> None:
        """Known placeholders should be replaced with their provided values."""
        result = render_template("Hi {first_name}!", {"first_name": "Ada"})
        assert result == "Hi Ada!"

    def test_render_template_leaves_unknown_placeholders(self) -> None:
        """Placeholders without a corresponding key should remain untouched."""
        result = render_template("Hi {unknown}!", {"first_name": "Ada"})
        assert result == "Hi {unknown}!"

    def test_format_duration_seconds(self) -> None:
        """Durations under a minute should render as seconds only."""
        assert format_duration(45) == "45s"

    def test_format_duration_hours_and_minutes(self) -> None:
        """Durations over an hour should render hours and remaining minutes."""
        assert format_duration(3660) == "1h 1m"

    def test_truncate_short_text_unchanged(self) -> None:
        """Text shorter than the limit should be returned unchanged."""
        assert truncate("hello", max_length=10) == "hello"

    def test_truncate_long_text_is_shortened(self) -> None:
        """Text longer than the limit should be truncated with an ellipsis."""
        result = truncate("hello world", max_length=5)
        assert len(result) <= 5
        assert result.endswith("…")

    def test_bulleted_list_formats_each_item(self) -> None:
        """Each item should be prefixed with a bullet on its own line."""
        assert bulleted_list(["a", "b"]) == "• a\n• b"


class TestHelpers:
    """Tests for general-purpose helper functions."""

    def test_chunk_list_splits_evenly(self) -> None:
        """A list divisible by the chunk size should split into equal chunks."""
        chunks = list(chunk_list([1, 2, 3, 4], 2))
        assert chunks == [[1, 2], [3, 4]]

    def test_chunk_list_handles_remainder(self) -> None:
        """A list not divisible by the chunk size should have a smaller final chunk."""
        chunks = list(chunk_list([1, 2, 3], 2))
        assert chunks == [[1, 2], [3]]

    def test_safe_int_parses_valid_string(self) -> None:
        """A valid numeric string should parse to its integer value."""
        assert safe_int("42") == 42

    def test_safe_int_returns_default_on_invalid_input(self) -> None:
        """An invalid string should fall back to the provided default."""
        assert safe_int("not-a-number", default=-1) == -1

    def test_deduplicate_preserve_order(self) -> None:
        """Duplicates should be removed while keeping first-seen order."""
        assert deduplicate_preserve_order([1, 2, 1, 3, 2]) == [1, 2, 3]

    def test_percentage_handles_zero_denominator(self) -> None:
        """Percentage of zero total should safely return 0.0 rather than raising."""
        assert percentage(5, 0) == 0.0

    def test_percentage_computes_correct_value(self) -> None:
        """Percentage should compute the correct rounded value."""
        assert percentage(1, 4) == 25.0


class TestParser:
    """Tests for command argument parsing helpers."""

    def test_parse_duration_minutes(self) -> None:
        """A duration like '10m' should parse to 600 seconds."""
        assert parse_duration("10m") == 600

    def test_parse_duration_invalid_returns_none(self) -> None:
        """An unparseable duration string should return None."""
        assert parse_duration("not-a-duration") is None

    def test_split_target_and_reason(self) -> None:
        """The first argument should become the target, the rest the reason."""
        target, reason = split_target_and_reason(["@user", "being", "rude"])
        assert target == "@user"
        assert reason == "being rude"

    def test_split_target_and_reason_empty(self) -> None:
        """Empty arguments should yield a None target and None reason."""
        target, reason = split_target_and_reason([])
        assert target is None
        assert reason is None

    def test_normalize_keyword(self) -> None:
        """Keywords should be lowercased and trimmed of surrounding whitespace."""
        assert normalize_keyword("  Hello ") == "hello"


class TestTime:
    """Tests for datetime helper functions."""

    def test_seconds_from_now_is_in_the_future(self) -> None:
        """The computed timestamp should be later than the current time."""
        future = seconds_from_now(60)
        assert future > datetime.now(timezone.utc)

    def test_is_expired_for_past_timestamp(self) -> None:
        """A timestamp in the past should be reported as expired."""
        past = datetime.now(timezone.utc) - timedelta(seconds=10)
        assert is_expired(past) is True

    def test_is_expired_for_future_timestamp(self) -> None:
        """A timestamp in the future should not be reported as expired."""
        future = datetime.now(timezone.utc) + timedelta(seconds=60)
        assert is_expired(future) is False
