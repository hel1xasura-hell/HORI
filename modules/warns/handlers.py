"""Handlers implementing the warning system: issue, remove, reset, and configure."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions, Message

from core.constants import DEFAULT_WARN_LIMIT, WarnAction
from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError, PermissionDeniedError, TargetUserNotFoundError
from core.logger import get_logger
from database.mongo import get_mongo_connection
from database.repositories.chat_repository import ChatRepository
from database.repositories.warn_repository import WarnRepository
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.parser import get_command_args
from utils.permissions import is_target_protected
from utils.users import extract_reason, get_user_mention, resolve_target_user

logger = get_logger(__name__)

_FULL_MUTE_PERMISSIONS = ChatPermissions(can_send_messages=False)


def _get_repositories() -> tuple[WarnRepository, ChatRepository]:
    """Build fresh repository instances bound to the active database.

    Returns:
        A tuple of `(WarnRepository, ChatRepository)`.
    """
    database = get_mongo_connection().get_database()
    return WarnRepository(database), ChatRepository(database)


async def _apply_warn_action(client: Client, message: Message, target_id: int, action: str) -> str:
    """Apply the configured action once a user reaches the warn limit.

    Args:
        client: The active Pyrogram client.
        message: The message the warn command was issued in.
        target_id: The Telegram user ID the action applies to.
        action: The `WarnAction` value describing what to do.

    Returns:
        A human-readable description of the action taken.
    """
    if action == WarnAction.BAN.value:
        await client.ban_chat_member(message.chat.id, target_id)
        return "banned"
    if action == WarnAction.KICK.value:
        await client.ban_chat_member(message.chat.id, target_id)
        await client.unban_chat_member(message.chat.id, target_id)
        return "kicked"
    if action == WarnAction.MUTE.value:
        await client.restrict_chat_member(message.chat.id, target_id, _FULL_MUTE_PERMISSIONS)
        return "muted"
    return "left unchanged"


@catch_errors
async def _handle_warn(client: Client, message: Message) -> None:
    """Issue a warning to a user, applying the configured action at the limit.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/warn` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")
    if is_target_protected(target.id):
        raise PermissionDeniedError("This user is protected and cannot be warned.")

    reason = extract_reason(message, offset=1) or "No reason given"

    warn_repo, chat_repo = _get_repositories()
    chat_settings = await chat_repo.get_or_create(message.chat.id, message.chat.title or "")
    updated_warn = await warn_repo.add_warning(message.chat.id, target.id, reason)

    if updated_warn.count >= chat_settings.warn_limit:
        action_text = await _apply_warn_action(client, message, target.id, chat_settings.warn_action)
        await warn_repo.reset(message.chat.id, target.id)
        await message.reply_text(
            f"⚠️ {get_user_mention(target)} reached {updated_warn.count}/{chat_settings.warn_limit} "
            f"warnings and has been <b>{action_text}</b>.\n<b>Reason:</b> {reason}"
        )
    else:
        await message.reply_text(
            f"⚠️ Warned {get_user_mention(target)} "
            f"({updated_warn.count}/{chat_settings.warn_limit}).\n<b>Reason:</b> {reason}"
        )

    logger.info("Warned user_id=%s in chat_id=%s (count=%s)", target.id, message.chat.id, updated_warn.count)


@catch_errors
async def _handle_warns(client: Client, message: Message) -> None:
    """Show a user's current warning count and reasons.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/warns` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        target = message.from_user

    warn_repo, chat_repo = _get_repositories()
    chat_settings = await chat_repo.get_or_create(message.chat.id, message.chat.title or "")
    warn_record = await warn_repo.get(message.chat.id, target.id)

    if warn_record.count == 0:
        await message.reply_text(f"{get_user_mention(target)} has no active warnings.")
        return

    reasons_text = "\n".join(f"{i + 1}. {reason}" for i, reason in enumerate(warn_record.reasons))
    await message.reply_text(
        f"⚠️ {get_user_mention(target)} has {warn_record.count}/{chat_settings.warn_limit} warnings:\n{reasons_text}"
    )


@catch_errors
async def _handle_unwarn(client: Client, message: Message) -> None:
    """Remove a single warning from a user.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unwarn` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")

    warn_repo, _ = _get_repositories()
    updated_warn = await warn_repo.remove_one_warning(message.chat.id, target.id)
    await message.reply_text(f"✅ Removed one warning from {get_user_mention(target)} ({updated_warn.count} remaining).")


@catch_errors
async def _handle_resetwarns(client: Client, message: Message) -> None:
    """Clear all of a user's warnings.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/resetwarns` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")

    warn_repo, _ = _get_repositories()
    await warn_repo.reset(message.chat.id, target.id)
    await message.reply_text(f"✅ Cleared all warnings for {get_user_mention(target)}.")


@catch_errors
async def _handle_warnlimit(client: Client, message: Message) -> None:
    """Set the number of warnings a user may accrue before action is taken.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/warnlimit` command message.
    """
    args = get_command_args(message)
    if not args or not args[0].isdigit() or int(args[0]) < 1:
        raise InvalidArgumentError("Usage: /warnlimit <number greater than 0>")

    new_limit = int(args[0])
    _, chat_repo = _get_repositories()
    await chat_repo.update_settings(message.chat.id, {"warn_limit": new_limit})
    await message.reply_text(f"✅ Warn limit set to {new_limit} (was {DEFAULT_WARN_LIMIT} by default).")


def register(client: Client) -> None:
    """Register all warns handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_warn, filters.command("warn") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_warns, filters.command("warns") & group_filter))
    client.add_handler(MessageHandler(_handle_unwarn, filters.command("unwarn") & group_filter & admin_filter))
    client.add_handler(
        MessageHandler(_handle_resetwarns, filters.command("resetwarns") & group_filter & admin_filter)
    )
    client.add_handler(
        MessageHandler(_handle_warnlimit, filters.command("warnlimit") & group_filter & admin_filter)
)
