"""Singleton MongoDB connection manager built on Motor's async driver."""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from core.exceptions import DatabaseConnectionError
from core.logger import get_logger

logger = get_logger(__name__)


class MongoConnection:
    """Manages a single, process-wide Motor client and database handle.

    This class should be instantiated once (via `get_mongo_connection`) and
    reused everywhere a database or collection handle is needed, avoiding the
    overhead of creating multiple client connections.
    """

    def __init__(self, uri: str, database_name: str) -> None:
        """Store connection parameters without opening a connection yet.

        Args:
            uri: The MongoDB connection URI.
            database_name: The name of the database to use.
        """
        self._uri = uri
        self._database_name = database_name
        self._client: AsyncIOMotorClient | None = None
        self._database: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Open the MongoDB client connection and verify it with a ping.

        Raises:
            DatabaseConnectionError: If the connection cannot be established
                or the ping check fails.
        """
        try:
            self._client = AsyncIOMotorClient(self._uri, serverSelectionTimeoutMS=10_000)
            self._database = self._client[self._database_name]
            await self.ping()
            logger.info("Connected to MongoDB database '%s'.", self._database_name)
        except PyMongoError as exc:
            raise DatabaseConnectionError(f"Failed to connect to MongoDB: {exc}") from exc

    async def ping(self) -> bool:
        """Ping the MongoDB server to confirm connectivity.

        Returns:
            True if the ping succeeds.

        Raises:
            DatabaseConnectionError: If the client has not been initialized,
                or the ping fails.
        """
        if self._client is None:
            raise DatabaseConnectionError("MongoDB client has not been initialized.")
        try:
            await self._client.admin.command("ping")
            return True
        except PyMongoError as exc:
            raise DatabaseConnectionError(f"MongoDB ping failed: {exc}") from exc

    def get_database(self) -> AsyncIOMotorDatabase:
        """Return the active database handle.

        Returns:
            The `AsyncIOMotorDatabase` instance for this connection.

        Raises:
            DatabaseConnectionError: If `connect()` has not been called yet.
        """
        if self._database is None:
            raise DatabaseConnectionError("Database has not been connected. Call connect() first.")
        return self._database

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Return a collection handle by name from the active database.

        Args:
            name: The name of the collection to retrieve.

        Returns:
            The `AsyncIOMotorCollection` instance for the given name.

        Raises:
            DatabaseConnectionError: If `connect()` has not been called yet.
        """
        return self.get_database()[name]

    def close(self) -> None:
        """Close the underlying MongoDB client connection."""
        if self._client is not None:
            self._client.close()
            logger.info("MongoDB connection closed.")
            self._client = None
            self._database = None


_connection: MongoConnection | None = None


def init_mongo_connection(uri: str, database_name: str) -> MongoConnection:
    """Create and store the process-wide `MongoConnection` singleton.

    Args:
        uri: The MongoDB connection URI.
        database_name: The name of the database to use.

    Returns:
        The newly created `MongoConnection` instance.
    """
    global _connection
    _connection = MongoConnection(uri=uri, database_name=database_name)
    return _connection


def get_mongo_connection() -> MongoConnection:
    """Return the process-wide `MongoConnection` singleton.

    Returns:
        The shared `MongoConnection` instance.

    Raises:
        DatabaseConnectionError: If `init_mongo_connection()` has not been called yet.
    """
    if _connection is None:
        raise DatabaseConnectionError("MongoDB connection has not been initialized.")
    return _connection
