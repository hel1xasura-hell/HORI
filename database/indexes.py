"""Index definitions and creation logic, applied once at startup."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING

from core.logger import get_logger

logger = get_logger(__name__)


async def ensure_indexes(database: AsyncIOMotorDatabase) -> None:
    """Create all required MongoDB indexes if they do not already exist.

    Index creation is idempotent: calling this function multiple times is
    safe and cheap once the indexes already exist.

    Args:
        database: The active Motor database handle.
    """
    await database["chats"].create_index([("chat_id", ASCENDING)], unique=True)
    await database["users"].create_index([("user_id", ASCENDING)], unique=True)

    await database["warns"].create_index(
        [("chat_id", ASCENDING), ("user_id", ASCENDING)], unique=True
    )

    await database["filters"].create_index(
        [("chat_id", ASCENDING), ("keyword", ASCENDING)], unique=True
    )

    await database["locks"].create_index([("chat_id", ASCENDING)], unique=True)

    await database["welcomes"].create_index([("chat_id", ASCENDING)], unique=True)

    await database["approvals"].create_index(
        [("chat_id", ASCENDING), ("user_id", ASCENDING)], unique=True
    )

    await database["connections"].create_index([("user_id", ASCENDING)], unique=True)

    await database["federations"].create_index([("federation_id", ASCENDING)], unique=True)
    await database["federations"].create_index([("owner_id", ASCENDING)])

    await database["flood_control"].create_index(
        [("chat_id", ASCENDING), ("user_id", ASCENDING)], unique=True
    )

    logger.info("All MongoDB indexes have been ensured.")
  
