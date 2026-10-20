"""
Database package for Intent-Aware Deception System.
"""

from backend.app.database.mongodb import get_db, mongodb_manager

__all__ = ["mongodb_manager", "get_db"]
