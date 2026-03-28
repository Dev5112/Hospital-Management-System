"""Database wrapper for the REST API.

Provides a simplified interface for database operations used by the API.
Uses the existing database setup from the root database.py module.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

class APIDatabase:
    """REST API database wrapper for HMS."""

    def __init__(self, db_path: str):
        """Initialize the API database wrapper.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        """Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection with row factory set
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def execute_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Execute query and return single row as dict.

        Args:
            query: SQL query with ? placeholders
            params: Query parameters

        Returns:
            Dictionary row or None if no results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None

    def execute_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return all rows as dicts.

        Args:
            query: SQL query with ? placeholders
            params: Query parameters

        Returns:
            List of dictionary rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def execute(self, query: str, params: tuple = ()) -> Optional[int]:
        """Execute INSERT/UPDATE/DELETE query.

        Args:
            query: SQL query with ? placeholders
            params: Query parameters

        Returns:
            Last row id for INSERT, None otherwise
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid if cursor.lastrowid else None

    def count(self, query: str, params: tuple = ()) -> int:
        """Execute COUNT query.

        Args:
            query: SQL query with COUNT(*)
            params: Query parameters

        Returns:
            Count of rows
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0

    def exists(self, query: str, params: tuple = ()) -> bool:
        """Check if query returns any rows.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            True if rows exist, False otherwise
        """
        return self.count(query, params) > 0
