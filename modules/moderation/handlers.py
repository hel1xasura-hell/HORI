"""Handlers implementing core moderation commands."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions, Message, User

from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError, PermissionDeniedError, TargetUserNotFoundError
from core.logger import get_logger
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.parser import get_command_args, parse_duration
from utils.permissions import can_bot_restrict_members, can_moderate, get_user_role, is_target_protected
from utils.time import seconds_from_now
from utils.users import extract_reason, get_user_mention, resolve_target_user

logger = get_logger(__name__)

_RESTRICTED_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_send_polls=False,
)

_UNMUTED_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_media_messages=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_send_polls=True,
)

_DURATION_UNITS = (("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1))


def _format_duration(seconds: int) -> str:
    """Render a duration in seconds as a short, human-readable token.

    Args:
        seconds: The duration to format.

    Returns:
        A compact string such as "10m" or "2h".
    """
    for suffix, unit_seconds in _DURATION_UNITS:
        if seconds >= unit_seconds and seconds % unit_seconds == 0:
            return f"{seconds // unit_seconds}{suffix}"
    return f"{seconds}s"


def _target_offset(message: Message) -> int:
    """Return how many leading argument tokens the target identifier occupies.

    A reply supplies the target implicitly, so no argument token is
    consumed by it; an explicit username/ID argument consumes exactly one.

    Args:
        message: The command message.

    Returns:
        0 if the command is a reply, else 1.
    """
    return 0 if message.reply_to_message else 1


def _parse_duration_and_reason(message: Message) -> tuple[int | None, str]:
    """Parse an optional leading duration token and the remaining reason text.

    This correctly handles both invocation styles:
        `/mute @user 10m spamming`  -> duration consumes args[1]
        `/mute 10m spamming` (reply) -> duration consumes args[0]

    Args:
        message: The command message.

    Returns:
        A `(duration_seconds, reason)` tuple. `duration_seconds` is None if
        no valid duration token was found at the expected position.
    """
    args = get_command_args(message)
    index = _target_offset(message)
    duration_seconds = parse_duration(args[index]) if len(args) > index else None
    reason_offset = index + (1 if duration_seconds is not None else 0)
    return duration_seconds, extract_reason(message, offset=reason_offset)


def _require_duration_and_reason(message: Message, usage: str) -> tuple[int, str]:
    """Parse a mandatory duration and reason, raising if none was given.

    Args:
        message: The command message.
        usage: The usage string to show if no valid duration is found.

    Returns:
        A `(duration_seconds, reason)` tuple.

    Raises:
        InvalidArgumentError: If no valid duration token was found.
    """
    duration_seconds, reason = _parse_duration_and_reason(message)
    if duration_seconds is None:
        raise InvalidArgumentError(usage)
    return duration_seconds, reason


async def _authorize_target(client: Client, message: Message) -> User:
    """Resolve a moderation target and verify the invoker outranks them.

    Args:
        client: The active Pyrogram client.
        message: The command message to resolve a target from.

    Returns:
        The resolved target `User`.

    Raises:
        TargetUserNotFoundError: If no target user could be resolved.
        PermissionDeniedError: If the target is protected, is the invoker
            themselves, or is not outranked by the invoker in Hori's
            Owner/SuperAdmin/Admin/Member hierarchy.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user's message or specify a valid username.")
    if is_target_protected(target.id):
        raise PermissionDeniedError("The bot owner cannot be moderated.")
    if message.from_user and target.id == message.from_user.id:
        raise PermissionDeniedError("You cannot moderate yourself.")

    actor_role = await get_user_role(client, message.chat.id, message.from_user.id)
    target_role = await get_user_role(client, message.chat.id, target.id)
    if not can_moderate(actor_role, target_role):
        raise PermissionDeniedError("You cannot moderate another administrator.")

    return target


@catch_errors
async def _handle_mute(client: Client, message: Message) -> None:
    """Restrict a user from sending messages, optionally for a fixed duration.

    Usage: /mute [reply|user] [duration] [reason]

    Args:
        client: The active Pyrogram client.
        message: The incoming `/mute` command message.
    """
    if not await can_bot_restrict_members(client, message.chat.id):
        raise PermissionDeniedError("I don't have enough permissions to perform this action.")

    target = await _authorize_target(client, message)
    duration_seconds, reason = _parse_duration_and_reason(message)

    until_date = seconds_from_now(duration_seconds) if duration_seconds else None
    await client.restrict_chat_member(
        message.chat.id, target.id, _RESTRICTED_PERMISSIONS, until_date=until_date
    )

    duration_text = f" for {_format_duration(duration_seconds)}" if duration_seconds else " indefinitely"
    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    await message.reply_text(f"🔇 Muted {get_user_mention(target)}{duration_text}.{reason_text}")
    logger.info("Muted user_id=%s in chat_id=%s (duration=%s)", target.id, message.chat.id, duration_seconds)


@catch_errors
async def _handle_tempmute(client: Client, message: Message) -> None:
    """Restrict a user from sending messages for a mandatory duration.

    Usage: /tempmute [reply|user] <duration> [reason]

    Args:
        client: The active Pyrogram client.
        message: The incoming `/tempmute` command message.
    """
    if not await can_bot_restrict_members(client, message.chat.id):
        raise PermissionDeniedError("I don't have enough permissions to perform this action.")

    target = await _authorize_target(client, message)
    duration_seconds, reason = _require_duration_and_reason(
        message, "Usage: /tempmute [reply|user] <duration e.g. 10m, 2h, 1d> [reason]"
    )

    until_date = seconds_from_now(duration_seconds)
    await client.restrict_chat_member(message.chat.id, target.id, _RESTRICTED_PERMISSIONS, until_date=until_date)

    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    await message.reply_text(
        f"🔇 Muted {get_user_mention(target)} for {_format_duration(duration_seconds)}.{reason_text}"
    )
    logger.info("Temp-muted user_id=%s in chat_id=%s (duration=%s)", target.id, message.chat.id, duration_seconds)


@catch_errors
async def _handle_unmute(client: Client, message: Message) -> None:
    """Restore a user's ability to send messages.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unmute` command message.
    """
    if not await can_bot_restrict_members(client, message.chat.id):
        raise PermissionDeniedError("I don't have enough permissions to perform this action.")

    target = await _authorize_target(client, message)
    await client.restrict_chat_member(message.chat.id, target.id, _UNMUTED_PERMISSIONS)
    await message.reply_text(f"🔊 Unmuted {get_user_mention(target)}.")
    logger.info("Unmuted user_id=%s in chat_id=%s", target.id, message.chat.id)


@catch_errors
async def _handle_kick(client: Client, message: Message) -> None:
    """Remove a user from the chat, allowing them to rejoin later.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/kick` command message.
    """
    target = await _authorize_target(client, message)
    reason = extract_reason(message, offset=_target_offset(message))

    await client.ban_chat_member(message.chat.id, target.id)
    await client.unban_chat_member(message.chat.id, target.id)

    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    await message.reply_text(f"👢 Kicked {get_user_mention(target)}.{reason_text}")
    logger.info("Kicked user_id=%s from chat_id=%s", target.id, message.chat.id)


@catch_errors
async def _handle_ban(client: Client, message: Message) -> None:
    """Permanently ban a user from the chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/ban` command message.
    """
    target = await _authorize_target(client, message)
    reason = extract_reason(message, offset=_target_offset(message))

    await client.ban_chat_member(message.chat.id, target.id)

    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    await message.reply_text(f"🔨 Banned {get_user_mention(target)}.{reason_text}")
    logger.info("Banned user_id=%s from chat_id=%s", target.id, message.chat.id)


@catch_errors
async def _handle_tempban(client: Client, message: Message) -> None:
    """Ban a user for a mandatory duration; Telegram lifts it automatically.

    Usage: /tempban [reply|user] <duration> [reason]

    Args:
        client: The active Pyrogram client.
        message: The incoming `/tempban` command message.
    """
    target = await _authorize_target(client, message)
    duration_seconds, reason = _require_duration_and_reason(
        message, "Usage: /tempban [reply|user] <duration e.g. 10m, 2h, 1d> [reason]"
    )

    until_date = seconds_from_now(duration_seconds)
    await client.ban_chat_member(message.chat.id, target.id, until_date=until_date)

    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    await message.reply_text(
        f"🔨 Banned {get_user_mention(target)} for {_format_duration(duration_seconds)}.{reason_text}"
    )
    logger.info("Temp-banned user_id=%s from chat_id=%s (duration=%s)", target.id, message.chat.id, duration_seconds)


@catch_errors
async def _handle_unban(client: Client, message: Message) -> None:
    """Lift a ban, allowing a user to rejoin the chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unban` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user's message or specify a valid username.")

    await client.unban_chat_member(message.chat.id, target.id)
    await message.reply_text(f"✅ Unbanned {get_user_mention(target)}.")
    logger.info("Unbanned user_id=%s in chat_id=%s", target.id, message.chat.id)


@catch_errors
async def _handle_pin(client: Client, message: Message) -> None:
    """Pin the message being replied to, optionally silently.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/pin` command message.
    """
    if not message.reply_to_message:
        raise TargetUserNotFoundError("Reply to the message you want to pin.")

    args = get_command_args(message)
    disable_notification = bool(args) and args[0].lower() in ("silent", "quiet", "s")

    await client.pin_chat_message(
        message.chat.id, message.reply_to_message.id, disable_notification=disable_notification
    )
    await message.reply_text("📌 Message pinned.")


@catch_errors
async def _handle_unpin(client: Client, message: Message) -> None:
    """Unpin the message being replied to, or the most recent pin if none.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unpin` command message.
    """
    if message.reply_to_message:
        await client.unpin_chat_message(message.chat.id, message.reply_to_message.id)
    else:
        await client.unpin_all_chat_messages(message.chat.id)
    await message.reply_text("📌 Message(s) unpinned.")


def register(client: Client) -> None:
    """Register all moderation handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_mute, filters.command("mute") & group_filter & admin_filter))
    client.add_handler(
        MessageHandler(_handle_tempmute, filters.command("tempmute") & group_filter & admin_filter)
    )
    client.add_handler(MessageHandler(_handle_unmute, filters.command("unmute") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_kick, filters.command("kick") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_ban, filters.command("ban") & group_filter & admin_filter))
    client.add_handler(
        MessageHandler(_handle_tempban, filters.command("tempban") & group_filter & admin_filter)
    )
    client.add_handler(MessageHandler(_handle_unban, filters.command("unban") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_pin, filters.command("pin") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_unpin, filters.command("unpin") & group_filter & admin_filter))
