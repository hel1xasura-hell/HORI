from __future__ import annotations

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import RPCError

from config.config import get_config

_ADMIN_STATUSES = (
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.OWNER,
)


async def is_user_chat_admin(
    client: Client,
    chat_id: int,
    user_id: int,
) -> bool:
    if user_id in get_config().privileged_users:
        return True

    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in _ADMIN_STATUSES
    except RPCError:
        return False


async def is_bot_chat_admin(
    client: Client,
    chat_id: int,
) -> bool:
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        return member.status in _ADMIN_STATUSES
    except RPCError:
        return False


async def can_bot_restrict_members(
    client: Client,
    chat_id: int,
) -> bool:
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)

        if member.status == ChatMemberStatus.OWNER:
            return True

        if member.status != ChatMemberStatus.ADMINISTRATOR:
            return False

        return bool(
            member.privileges
            and member.privileges.can_restrict_members
        )

    except RPCError:
        return False


async def can_moderate(
    client: Client,
    chat_id: int,
    user_id: int,
) -> bool:
    """
    Returns True if the user can use moderation commands.
    """

    return await is_user_chat_admin(
        client,
        chat_id,
        user_id,
    )


async def get_user_role(
    client: Client,
    chat_id: int,
    user_id: int,
) -> str:
    """
    Returns:
        owner
        superadmin
        admin
        member
    """

    config = get_config()

    if user_id == config.owner_id:
        return "owner"

    if user_id in config.sudo_users:
        return "superadmin"

    try:
        member = await client.get_chat_member(chat_id, user_id)

        if member.status == ChatMemberStatus.OWNER:
            return "owner"

        if member.status == ChatMemberStatus.ADMINISTRATOR:
            return "admin"

    except RPCError:
        pass

    return "member"


def is_target_protected(
    target_user_id: int,
) -> bool:
    """
    Protect owner and superadmins from moderation.
    """

    return target_user_id in get_config().privileged_users
