"""
MongoDB Connection Manager and Indexing Service.
Provides a resilient singleton MongoClient, health checking, and automatic index creation.
"""

import logging
from typing import Any, Optional
from pymongo import ASCENDING, DESCENDING, IndexModel, MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, PyMongoError

from backend.app.config import settings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """
    Manages the lifecycle of the PyMongo client, database handles, and collection indexes.
    """

    def __init__(self, uri: Optional[str] = None, database_name: Optional[str] = None):
        self.uri = uri or settings.MONGODB_URI
        self.database_name = database_name or settings.DATABASE_NAME
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None

    def connect(self) -> Database:
        """
        Establishes connection to MongoDB and creates necessary indexes.
        """
        if self._db is not None:
            return self._db

        try:
            logger.info("Connecting to MongoDB database: '%s'...", self.database_name)
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=3000,
                connectTimeoutMS=3000
            )
            # Verify connectivity
            self._client.admin.command("ping")
            self._db = self._client[self.database_name]
            logger.info("Successfully connected to MongoDB.")

            self.create_indexes()
            return self._db

        except (ConnectionFailure, PyMongoError) as e:
            logger.error("Failed to connect to MongoDB: %s", e)
            self._db = None
            raise

    def get_database(self) -> Database:
        """
        Retrieves the active database instance, connecting if necessary.
        """
        if self._db is None:
            return self.connect()
        return self._db

    def check_health(self) -> bool:
        """
        Performs a ping command to verify database health.
        """
        if self._client is None:
            try:
                self.connect()
            except Exception:
                return False

        try:
            self._client.admin.command("ping")
            return True
        except Exception as e:
            logger.warning("MongoDB health check failed: %s", e)
            return False

    def create_indexes(self) -> None:
        """
        Ensures optimal indexes exist for events, sessions, attackers, and alerts collections.
        """
        if self._db is None:
            return

        try:
            # Events collection indexes
            events_col = self._db["events"]
            events_col.create_indexes([
                IndexModel([("event_id", ASCENDING)], unique=True),
                IndexModel([("session_id", ASCENDING)]),
                IndexModel([("timestamp", DESCENDING)]),
                IndexModel([("source_ip", ASCENDING)]),
                IndexModel([("intent", ASCENDING)]),
                IndexModel([("severity", ASCENDING)]),
                IndexModel([("risk_score", DESCENDING)])
            ])

            # Sessions collection indexes
            sessions_col = self._db["sessions"]
            sessions_col.create_indexes([
                IndexModel([("session_id", ASCENDING)], unique=True),
                IndexModel([("source_ip", ASCENDING)]),
                IndexModel([("last_seen", DESCENDING)]),
                IndexModel([("dominant_intent", ASCENDING)]),
                IndexModel([("severity", ASCENDING)]),
                IndexModel([("risk_score", DESCENDING)])
            ])

            # Attackers collection indexes
            attackers_col = self._db["attackers"]
            attackers_col.create_indexes([
                IndexModel([("source_ip", ASCENDING)], unique=True),
                IndexModel([("last_seen", DESCENDING)]),
                IndexModel([("maximum_risk", DESCENDING)]),
                IndexModel([("severity", ASCENDING)])
            ])

            # Alerts collection indexes
            alerts_col = self._db["alerts"]
            alerts_col.create_indexes([
                IndexModel([("alert_id", ASCENDING)], unique=True),
                IndexModel([("session_id", ASCENDING)]),
                IndexModel([("timestamp", DESCENDING)]),
                IndexModel([("severity", ASCENDING)]),
                IndexModel([("status", ASCENDING)])
            ])

            logger.info("MongoDB indexes verified successfully.")
        except Exception as e:
            logger.error("Error creating MongoDB indexes: %s", e)

    def close(self) -> None:
        """
        Gracefully closes the MongoDB connection.
        """
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB connection closed.")


# Singleton instance
mongodb_manager = MongoDBManager()


def get_db() -> Database:
    """
    Dependency helper returning the current active database.
    """
    return mongodb_manager.get_database()
