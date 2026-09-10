"""
Unit tests for MongoDB Connection Manager and Indexing.
"""

from unittest.mock import MagicMock, patch
import pytest
from pymongo.errors import ConnectionFailure

from backend.app.database.mongodb import MongoDBManager


def test_mongodb_manager_connect_and_health():
    with patch("backend.app.database.mongodb.MongoClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.admin.command.return_value = {"ok": 1.0}
        mock_client_cls.return_value = mock_client

        mgr = MongoDBManager(uri="mongodb://mock:27017", database_name="test_deception_db")
        db = mgr.connect()

        assert db is not None
        assert mgr.check_health() is True
        mock_client.admin.command.assert_called_with("ping")

        mgr.close()
        assert mgr._client is None


def test_mongodb_manager_connection_failure():
    with patch("backend.app.database.mongodb.MongoClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.admin.command.side_effect = ConnectionFailure("Connection refused")
        mock_client_cls.return_value = mock_client

        mgr = MongoDBManager(uri="mongodb://invalid:27017", database_name="test_deception_db")
        with pytest.raises(ConnectionFailure):
            mgr.connect()

        assert mgr.check_health() is False
