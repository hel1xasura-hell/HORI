"""Handlers for configuring and enforcing chat content locks."""

from __future__ import annotations

from typing import Callable, Dict

from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from core.constants import LockableType
from core.decorators import catch_errors
from core.exceptions import InvalidArgumentError
from core.logger import get_logger
from database.mongo import get_mongo_connection
from database.repositories.approval_repository import ApprovalRepository
from database.repositories.lock_repository import LockRepository
from filters.admin import admin_filter
from filters.chat import group_filter
from utils.formatting import bulleted_list
from utils.parser import get_command_args
from utils.permissions import is_user_chat_admin

logger = get_logger(__name__)

_LOCK_CHECKS: Dict[str, Callable[[Message], bool]] = {
    LockableType.TEXT.value: lambda m: bool(m.text) and not m.text.startswith(("/", "!")),
    LockableType.MEDIA.value: lambda m: bool(m.photo or m.video or m.audio or m.document),
    LockableType.STICKER.value: lambda m: bool(m.sticker),
    LockableType.GIF.value: lambda m: bool(m.animation),
    LockableType.URL.value: lambda m: bool(m.entities) and any(e.type.name in ("URL", "TEXT_LINK") for e in (m.entities or [])),
    LockableType.FORWARD.value: lambda m: bool(m.forward_date),
    LockableType.POLL.value: lambda m: bool(m.poll),
    LockableType.GAME.value: lambda m: bool(m.game),
    LockableType.LOCATION.value: lambda m: bool(m.location or m.venue),
    LockableType.CONTACT.value: lambda m: bool(m.contact),
    LockableType.COMMANDS.value: lambda m: bool(m.text) and m.text.startswith(("/", "!")),
    LockableType.BOTS.value: lambda m: False,
    LockableType.INLINE.value: lambda m: bool(m.via_bot),
}

_VALID_TYPES = {member.value for member in LockableType}


def _get_repositories() -> tuple[LockRepository, ApprovalRepository]:
    """Build fresh repository instances bound to the active database.

    Returns:
        A tuple of `(LockRepository, ApprovalRepository)`.
    """
    database = get_mongo_connection().get_database()
    return LockRepository(database), ApprovalRepository(database)


@catch_errors
async def _handle_lock(client: Client, message: Message) -> None:
    """Lock a content type in this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/lock` command message.
    """
    args = get_command_args(message)
    if not args or args[0].lower() not in _VALID_TYPES:
        raise InvalidArgumentError(f"Usage: /lock <type>\nValid types: {', '.join(sorted(_VALID_TYPES))}")

    lock_type = args[0].lower()
    lock_repo, _ = _get_repositories()
    await lock_repo.lock(message.chat.id, lock_type)
    await message.reply_text(f"🔒 Locked <code>{lock_type}</code> in this chat.")


@catch_errors
async def _handle_unlock(client: Client, message: Message) -> None:
    """Unlock a content type in this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/unlock` command message.
    """
    args = get_command_args(message)
    if not args or args[0].lower() not in _VALID_TYPES:
        raise InvalidArgumentError(f"Usage: /unlock <type>\nValid types: {', '.join(sorted(_VALID_TYPES))}")

    lock_type = args[0].lower()
    lock_repo, _ = _get_repositories()
    await lock_repo.unlock(message.chat.id, lock_type)
    await message.reply_text(f"🔓 Unlocked <code>{lock_type}</code> in this chat.")


@catch_errors
async def _handle_list_locks(client: Client, message: Message) -> None:
    """List all content types currently locked in this chat.

    Args:
        client: The active Pyrogram client.
        message: The incoming `/locks` command message.
    """
    lock_repo, _ = _get_repositories()
    locks = await lock_repo.get(message.chat.id)
    if not locks.locked_types:
        await message.reply_text("No locks are currently active in this chat.")
        return
    await message.reply_text(f"🔒 <b>Active locks:</b>\n{bulleted_list(sorted(locks.locked_types))}")


@catch_errors
async def _handle_enforce_locks(client: Client, message: Message) -> None:
    """Delete a message if it violates an active content lock.

    Admins and approved users are exempt from lock enforcement.

    Args:
        client: The active Pyrogram client.
        message: The incoming message to check against active locks.
    """
    if message.from_user is None:
        return

    if await is_user_chat_admin(client, message.chat.id, message.from_user.id):
        return

    lock_repo, approval_repo = _get_repositories()
    locks = await lock_repo.get(message.chat.id)
    if not locks.locked_types:
        return

    if await approval_repo.is_approved(message.chat.id, message.from_user.id):
        return

    for lock_type in locks.locked_types:
        check = _LOCK_CHECKS.get(lock_type)
        if check and check(message):
            try:
                await message.delete()
            except RPCError:
                logger.debug("Failed to delete locked-content message; may already be gone.")
            return


def register(client: Client) -> None:
    """Register all lock handlers on the given client.

    Args:
        client: The Pyrogram client to attach the handlers to.
    """
    client.add_handler(MessageHandler(_handle_lock, filters.command("lock") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_unlock, filters.command("unlock") & group_filter & admin_filter))
    client.add_handler(MessageHandler(_handle_list_locks, filters.command("locks") & group_filter))
    client.add_handler(MessageHandler(_handle_enforce_locks, group_filter & filters.incoming))
