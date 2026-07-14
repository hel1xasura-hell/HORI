"""Factory for constructing the Pyrogram `Client` instance.

Client construction is intentionally separated from application startup so
that the client can be created, configured, and tested independently of the
rest of the bootstrap sequence.
"""

from __future__ import annotations

from pyrogram import Client

from config.config import Config
from core.logger import get_logger

logger = get_logger(__name__)


def create_bot_client(config: Config) -> Client:
    """Construct a configured Pyrogram `Client` for the bot.

    Args:
        config: The application configuration containing API credentials.

    Returns:
        A `Client` instance ready to be started. The client is not started
        by this function; the caller is responsible for its lifecycle.
    """
    client = Client(
        name=config.session_name,
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
        workers=config.workers,
        parse_mode=config.parse_mode,
        in_memory=True,
    )
    logger.debug("Pyrogram client '%s' constructed.", config.session_name)
    return client

