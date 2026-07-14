"""Handlers implementing core moderation commands."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions, Message, User

from core.decorators import catch_errors
from core.exceptions import PermissionDeniedError, TargetUserNotFoundError
from core.logger import get_logger
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.parser import get_command_args, parse_duration
from utils.permissions import can_bot_restrict_members, is_target_protected
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


async def _require_target(client: Client, message: Message) -> User:
    """Resolve a moderation target, raising a clear error if none is found.

    Args:
        client: The active Pyrogram client.
        message: The command message to resolve a target from.

    Returns:
        The resolved target `User`.

    Raises:
        TargetUserNotFoundError: If no target user could be resolved.
        PermissionDeniedError: If the resolved target is a protected user.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")
    if is_target_protected(target.id):
        raise PermissionDeniedError("This user is protected and cannot be moderated.")
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
        raise PermissionDeniedError("I need 'Restrict Members' permission to mute users.")

    target = await _require_target(client, message)
    args = get_command_args(message)
    duration_seconds = parse_duration(args[0]) if args and not message.reply_to_message else None
    reason_offset = 2 if (args and duration_seconds is not None) else 1
    reason = extract_reason(message, offset=reason_offset)

    until_date = seconds_from_now(duration_seconds) if duration_seconds else None
    await client.restrict_chat_member(
        message.chat.id, target.id, _RESTRICTED_PERMISSIONS, until_date=until_date
    )

    duration_text = f" for {args[0]}" if duration_seconds else " indefinitely"
    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    await message.reply_text(f"🔇 Muted {get_user_mention(target)}{duration_text}.{reason_text}")
    logger.info("Muted user_id=%s in chat_id=%s", target.id, message.chat.id)


@catch_errors
async def _handle_unmute(client: Client, message: Message) -> None:
    """Restore a user's ability to send messages.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unmute` command message.
    """
    if not await can_bot_restrict_members(client, message.chat.id):
        raise PermissionDeniedError("I need 'Restrict Members' permission to unmute users.")

    target = await _require_target(client, message)
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
    target = await _require_target(client, message)
    reason = extract_reason(message, offset=1)

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
    target = await _require_target(client, message)
    reason = extract_reason(message, offset=1)

    await client.ban_chat_member(message.chat.id, target.id)

    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    await message.reply_text(f"🔨 Banned {get_user_mention(target)}.{reason_text}")
    logger.info("Banned user_id=%s from chat_id=%s", target.id, message.chat.id)


@catch_errors
async def _handle_unban(client: Client, message: Message) -> None:
    """Lift a ban, allowing a user to rejoin the chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unban` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")

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


@catch_errors
async def _handle_purge(client: Client, message: Message) -> None:
    """Delete every message between the replied-to message and this command.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/purge` command message.
    """
    if not message.reply_to_message:
        raise TargetUserNotFoundError("Reply to the message you want to purge from.")

    start_id = message.reply_to_message.id
    end_id = message.id
    message_ids = list(range(start_id, end_id + 1))

    deleted_count = 0
    for batch_start in range(0, len(message_ids), 100):
        batch = message_ids[batch_start : batch_start + 100]
        try:
            await client.delete_messages(message.chat.id, batch)
            deleted_count += len(batch)
        except RPCError:
            logger.debug("Some messages in purge batch could not be deleted; continuing.")

    logger.info("Purged %d messages in chat_id=%s", deleted_count, message.chat.id)


def register(client: Client) -> None:
    """Register all moderation handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    base_filter = filters.command("mute") & group_filter & admin_filter
    client.add_handler(MessageHandler(_handle_mute, base_filter))
    client.add_handler(MessageHandler(_handle_unmute, filters.command("unmute") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_kick, filters.command("kick") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_ban, filters.command("ban") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_unban, filters.command("unban") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_pin, filters.command("pin") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_unpin, filters.command("unpin") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_purge, filters.command("purge") & group_filter & admin_filter))

