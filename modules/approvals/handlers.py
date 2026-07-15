"""Handlers for approving, revoking, and listing trusted chat members."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.decorators import catch_errors
from core.exceptions import TargetUserNotFoundError
from core.logger import get_logger
from database.models.approval import Approval
from database.mongo import get_mongo_connection
from database.repositories.approval_repository import ApprovalRepository
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.formatting import bulleted_list
from utils.users import get_user_mention, resolve_target_user

logger = get_logger(__name__)


def _get_repository() -> ApprovalRepository:
    """Build a fresh `ApprovalRepository` bound to the active database.

    Returns:
        An `ApprovalRepository` instance.
    """
    return ApprovalRepository(get_mongo_connection().get_database())


@catch_errors
async def _handle_approve(client: Client, message: Message) -> None:
    """Approve a user, exempting them from locks and antispam in this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/approve` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")

    approval = Approval(chat_id=message.chat.id, user_id=target.id, approved_by=message.from_user.id)
    await _get_repository().approve(approval)
    await message.reply_text(f"✅ {get_user_mention(target)} is now approved and exempt from locks/antispam.")


@catch_errors
async def _handle_unapprove(client: Client, message: Message) -> None:
    """Revoke a user's approval status in this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unapprove` command message.
    """
    target = await resolve_target_user(client, message)
    if target is None:
        raise TargetUserNotFoundError("Reply to a user or provide their @username/ID.")

    revoked = await _get_repository().revoke(message.chat.id, target.id)
    if revoked:
        await message.reply_text(f"✅ Approval revoked for {get_user_mention(target)}.")
    else:
        await message.reply_text(f"{get_user_mention(target)} was not approved.")


@catch_errors
async def _handle_list_approved(client: Client, message: Message) -> None:
    """List all users approved in this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/approved` command message.
    """
    approvals = await _get_repository().list_for_chat(message.chat.id)
    if not approvals:
        await message.reply_text("No users are currently approved in this chat.")
        return

    entries = [f"<a href=\"tg://user?id={a.user_id}\">{a.user_id}</a>" for a in approvals]
    await message.reply_text(f"✅ <b>Approved users:</b>\n{bulleted_list(entries)}")


def register(client: Client) -> None:
    """Register all approval handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_approve, filters.command("approve") & group_filter & admin_filter))
    client.add_handler(
        MessageHandler(_handle_unapprove, filters.command("unapprove") & group_filter & admin_filter)
    )
    client.add_handler(MessageHandler(_handle_list_approved, filters.command("approved") & group_filter))
