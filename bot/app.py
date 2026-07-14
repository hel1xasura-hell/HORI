"""Top-level application container tying together the client, database,
scheduler, and all feature modules.
"""

from __future__ import annotations

from pyrogram import Client, idle

from bot.client import create_bot_client
from config.config import Config
from core.constants import BOT_NAME, BOT_VERSION
from core.logger import get_logger
from core.scheduler import BotScheduler, get_scheduler
from database.mongo import MongoConnection, get_mongo_connection

logger = get_logger(__name__)


class Application:
    """Owns the full lifecycle of the Hori bot process.

    This class is the single place responsible for starting and stopping
    every subsystem (database, scheduler, Pyrogram client) in the correct
    order, and for registering all feature-module handlers on the client.
    """

    def __init__(self, config: Config) -> None:
        """Initialize the application with its configuration.

        Args:
            config: The validated application configuration.
        """
        self._config = config
        self._client: Client = create_bot_client(config)
        self._scheduler: BotScheduler = get_scheduler()
        self._mongo: MongoConnection | None = None

    @property
    def client(self) -> Client:
        """Return the underlying Pyrogram client instance."""
        return self._client

    async def start(self) -> None:
        """Start the client and scheduler, then register all handlers.

        Assumes the database connection has already been established by
        `core.startup` prior to calling this method.
        """
        self._mongo = get_mongo_connection()

        self._register_handlers()

        await self._client.start()
        self._scheduler.start()

        bot_identity = await self._client.get_me()
        logger.info(
            "%s v%s is now online as @%s (id=%s).",
            BOT_NAME,
            BOT_VERSION,
            bot_identity.username,
            bot_identity.id,
        )

    async def stop(self) -> None:
        """Gracefully stop the scheduler and the Pyrogram client."""
        if self._scheduler.is_running:
            self._scheduler.shutdown(wait=True)

        await self._client.stop()
        logger.info("%s has been stopped.", BOT_NAME)

    async def idle(self) -> None:
        """Block until an OS termination signal is received."""
        await idle()

    def _register_handlers(self) -> None:
        """Import and register every handler group with the Pyrogram client.

        Handlers are imported lazily, inside this method, so that they are
        only bound to the running client instance and never registered twice.
        """
        from handlers import help as help_handlers
        from handlers import start as start_handlers
        from modules.antispam import handlers as antispam_handlers
        from modules.approvals import handlers as approvals_handlers
        from modules.connections import handlers as connections_handlers
        from modules.federations import handlers as federations_handlers
        from modules.filters import handlers as filters_handlers
        from modules.locks import handlers as locks_handlers
        from modules.misc import handlers as misc_handlers
        from modules.moderation import handlers as moderation_handlers
        from modules.reports import handlers as reports_handlers
        from modules.warns import handlers as warns_handlers
        from modules.welcomes import handlers as welcomes_handlers

        registrars = (
            start_handlers.register,
            help_handlers.register,
            moderation_handlers.register,
            warns_handlers.register,
            welcomes_handlers.register,
            filters_handlers.register,
            locks_handlers.register,
            antispam_handlers.register,
            reports_handlers.register,
            approvals_handlers.register,
            connections_handlers.register,
            federations_handlers.register,
            misc_handlers.register,
        )

        for registrar in registrars:
            registrar(self._client)

        logger.info("Registered %d handler modules.", len(registrars))
