"""Handler that lets chat members report a message to the group's admins."""

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError
from core.logger import get_logger
from filters.chat import group_filter
from utils.users import extract_reason, get_user_mention

logger = get_logger(__name__)


@catch_errors
async def _handle_report(client: Client, message: Message) -> None:
    """Notify chat administrators about a reported message.

    Usage: reply to the offending message with /report [reason].

    Args:
        client: The active Pyrogram client.
        message: The incoming `/report` command message.
    """
    if not message.reply_to_message or not message.reply_to_message.from_user:
        raise InvalidArgumentError("Reply to the message you want to report.")

    reported_user = message.reply_to_message.from_user
    reporter = message.from_user
    reason = extract_reason(message, offset=1)

    admin_mentions = []
    async for member in client.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
        if not member.user.is_bot:
            admin_mentions.append(get_user_mention(member.user))

    if not admin_mentions:
        await message.reply_text("⚠️ Could not find any administrators to notify.")
        return

    reason_text = f"\n<b>Reason:</b> {reason}" if reason else ""
    notification = (
        f"🚨 <b>Report</b>\n"
        f"{', '.join(admin_mentions)}\n"
        f"{get_user_mention(reporter)} reported {get_user_mention(reported_user)}.{reason_text}"
    )

    try:
        await message.reply_to_message.reply_text(notification)
    except RPCError:
        await message.reply_text(notification)

    logger.info(
        "User_id=%s reported user_id=%s in chat_id=%s", reporter.id, reported_user.id, message.chat.id
    )


def register(client: Client) -> None:
    """Register the report handler on the given client.

    Args:
        client: The Pyrogram client to attach the handler to.
    """
    client.add_handler(
        MessageHandler(_handle_report, filters.command("report") & group_filter)
)
  
