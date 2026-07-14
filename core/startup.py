"""Orchestrates the full application startup and shutdown sequence.

Startup order: config -> logging -> database -> indexes -> scheduler ->
Pyrogram client -> handler registration -> idle -> graceful shutdown.
"""

from __future__ import annotations

from bot.app import Application
from config.config import Config, get_config
from core.exceptions import HoriError
from core.logger import get_logger, setup_logging
from database.indexes import ensure_indexes
from database.mongo import init_mongo_connection

logger = get_logger(__name__)


async def run_application() -> None:
    """Run the Hori bot end-to-end: startup, idle, and graceful shutdown.

    Raises:
        HoriError: If any stage of startup fails in a way that prevents the
            bot from running.
    """
    config = _bootstrap_config_and_logging()

    mongo_connection = init_mongo_connection(uri=config.mongo_uri, database_name=config.mongo_db_name)
    await mongo_connection.connect()
    await ensure_indexes(mongo_connection.get_database())

    application = Application(config)

    try:
        await application.start()
        await application.idle()
    except HoriError:
        logger.exception("A fatal application error occurred during runtime.")
        raise
    finally:
        await _shutdown(application, mongo_connection)


def _bootstrap_config_and_logging() -> Config:
    """Load configuration and initialize logging as the very first startup step.

    Returns:
        The loaded and validated application `Config`.

    Raises:
        HoriError: If configuration loading fails.
    """
    try:
        config = get_config()
    except Exception as exc:  # noqa: BLE001 - config errors must never crash silently
        # Logging isn't configured yet, so fall back to a bare print for this
        # one, unrecoverable case.
        print(f"FATAL: failed to load configuration: {exc}")
        raise HoriError(f"Failed to load configuration: {exc}") from exc

    setup_logging(config.log_level)
    logger.info("Configuration loaded and logging initialized (environment=%s).", config.environment)
    return config


async def _shutdown(application: Application, mongo_connection) -> None:  # type: ignore[no-untyped-def]
    """Perform an orderly shutdown of the client, scheduler, and database.

    Args:
        application: The running `Application` instance.
        mongo_connection: The active `MongoConnection` instance to close.
    """
    logger.info("Shutting down Hori...")
    try:
        await application.stop()
    except Exception:  # noqa: BLE001 - shutdown must proceed regardless
        logger.exception("Error while stopping the application; continuing shutdown.")

    mongo_connection.close()
    logger.info("Shutdown complete.")
