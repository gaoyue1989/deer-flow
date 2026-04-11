"""Database-backed user store that uses checkpointer database.

This module provides a database-backed user store that uses the same
database as the checkpointer, but creates its own connection for
synchronous operations.

Supported backends:
- memory: In-memory SQLite
- sqlite: SQLite database file (creates separate sync connection)
- postgres: PostgreSQL database (creates separate sync connection)
- mysql: MySQL database (creates separate sync connection)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from app.gateway.auth.models import UserRole
from deerflow.config.checkpointer_config import get_checkpointer_config, CheckpointerConfig
from deerflow.runtime.store._sqlite_utils import resolve_sqlite_conn_str, ensure_sqlite_parent_dir

logger = logging.getLogger(__name__)


class DBUserStore:
    """Database-backed user store that uses checkpointer database.

    This reads the checkpointer configuration and creates a separate
    connection to the same database for user storage operations.
    """

    def __init__(self) -> None:
        """Initialize the database user store.

        Reads checkpointer configuration and creates a connection to the
        same database for user storage.
        """
        config = get_checkpointer_config()
        if config is None:
            config = CheckpointerConfig(type="memory")

        self._config = config
        self._lock = threading.Lock()
        self._conn = None
        self._is_sqlite = False
        self._is_mysql = False
        self._pool = None
        self._initialize_connection()
        self._create_table_if_not_exists()

    def _initialize_connection(self) -> None:
        """Initialize the database connection based on backend type."""
        if self._config.type == "memory":
            self._init_memory()
        elif self._config.type == "sqlite":
            self._init_sqlite()
        elif self._config.type == "postgres":
            self._init_postgres()
        elif self._config.type == "mysql":
            self._init_mysql()
        else:
            raise ValueError(f"Unknown database type: {self._config.type}")

    def _init_memory(self) -> None:
        """Initialize in-memory SQLite database."""
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._is_sqlite = True

    def _init_sqlite(self) -> None:
        """Initialize SQLite database from config."""
        if not self._config.connection_string:
            raise ValueError("connection_string is required for sqlite backend")

        conn_str = resolve_sqlite_conn_str(self._config.connection_string)
        ensure_sqlite_parent_dir(conn_str)
        self._conn = sqlite3.connect(conn_str, check_same_thread=False)
        self._is_sqlite = True

    def _init_postgres(self) -> None:
        """Initialize PostgreSQL database from config."""
        import psycopg

        if not self._config.connection_string:
            raise ValueError("connection_string is required for postgres backend")

        self._conn = psycopg.connect(self._config.connection_string)
        self._is_sqlite = False

    def _init_mysql(self) -> None:
        """Initialize MySQL database from config."""
        import pymysql

        if not self._config.connection_string:
            raise ValueError("connection_string is required for mysql backend")

        # Parse connection string: mysql://user:password@host:port/dbname
        conn_str = self._config.connection_string
        if conn_str.startswith("mysql://"):
            conn_str = conn_str[8:]

        # Parse user:password@host:port/dbname
        user_pass, rest = conn_str.split("@", 1)
        user, password = user_pass.split(":", 1)
        host_port_db = rest.split("/")
        host_port = host_port_db[0].split(":")
        dbname = host_port_db[1] if len(host_port_db) > 1 else ""

        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306

        self._conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=dbname,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            init_command="SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
        )
        self._is_sqlite = False
        self._is_mysql = True

    def _create_table_if_not_exists(self) -> None:
        """Create the users table if it doesn't already exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(36) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NOT NULL,
            %s
        );
        """
        create_index_sql = "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);"

        if self._is_sqlite:
            quota_def = "quota_limits JSON DEFAULT '{}'"
        elif self._is_mysql:
            # MySQL doesn't allow DEFAULT for JSON columns
            quota_def = "quota_limits JSON"
        else:
            quota_def = "quota_limits JSONB DEFAULT '{}'::JSONB"

        with self._lock:
            if self._is_sqlite:
                cursor = self._conn.cursor()
                cursor.execute(create_table_sql % quota_def)
                cursor.execute(create_index_sql)
                self._conn.commit()
            elif self._is_mysql:
                cursor = self._conn.cursor()
                cursor.execute(create_table_sql % quota_def)
                # MySQL doesn't support IF NOT EXISTS for indexes
                try:
                    cursor.execute("CREATE INDEX idx_users_email ON users(email);")
                except Exception:
                    pass  # Index already exists
                self._conn.commit()
            else:
                with self._conn.cursor() as cur:
                    cur.execute(create_table_sql % quota_def)
                    cur.execute(create_index_sql)
                    self._conn.commit()

    def get_by_id(self, user_id: UUID | str) -> Optional[dict[str, Any]]:
        """Get a user by ID."""
        user_id_str = str(user_id) if isinstance(user_id, UUID) else user_id

        with self._lock:
            if self._is_sqlite:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE user_id = ?", (user_id_str,))
                row = cursor.fetchone()
            elif self._is_mysql:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE user_id = %s", (user_id_str,))
                row = cursor.fetchone()
            else:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE user_id = %s", (user_id_str,))
                    row = cur.fetchone()

            if not row:
                return None

            return self._row_to_dict(row)

    def get_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """Get a user by email."""
        with self._lock:
            if self._is_sqlite:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
            elif self._is_mysql:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE email = %s", (email,))
                row = cursor.fetchone()
            else:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE email = %s", (email,))
                    row = cur.fetchone()

            if not row:
                return None

            return self._row_to_dict(row)

    def create(
        self,
        user_id: UUID,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        quota_limits: Optional[dict[str, int | float]] = None,
    ) -> dict[str, Any]:
        """Create a new user."""
        with self._lock:
            user_id_str = str(user_id)
            created_at = datetime.utcnow().isoformat()

            if quota_limits is None:
                quota_limits = self._get_default_quotas(role)

            quota_json = json.dumps(quota_limits)

            if self._is_sqlite:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id_str,))
                if cursor.fetchone() is not None:
                    raise ValueError(f"User ID {user_id_str} already exists")

                cursor.execute("SELECT user_id FROM users WHERE email = ?", (email,))
                if cursor.fetchone() is not None:
                    raise ValueError(f"Email {email} already registered")

                cursor.execute(
                    """
                    INSERT INTO users (user_id, email, hashed_password, role, created_at, quota_limits)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id_str, email, hashed_password, role.value, created_at, quota_json),
                )
                self._conn.commit()
            elif self._is_mysql:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id_str,))
                if cursor.fetchone() is not None:
                    raise ValueError(f"User ID {user_id_str} already exists")

                cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                if cursor.fetchone() is not None:
                    raise ValueError(f"Email {email} already registered")

                cursor.execute(
                    """
                    INSERT INTO users (user_id, email, hashed_password, role, created_at, quota_limits)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id_str, email, hashed_password, role.value, created_at, quota_json),
                )
                self._conn.commit()
            else:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id_str,))
                    if cur.fetchone() is not None:
                        raise ValueError(f"User ID {user_id_str} already exists")

                    cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                    if cur.fetchone() is not None:
                        raise ValueError(f"Email {email} already registered")

                    cur.execute(
                        """
                        INSERT INTO users (user_id, email, hashed_password, role, created_at, quota_limits)
                        VALUES (%s, %s, %s, %s, %s, %s::JSONB)
                        """,
                        (user_id_str, email, hashed_password, role.value, created_at, quota_json),
                    )
                    self._conn.commit()

            return {
                "user_id": user_id_str,
                "email": email,
                "hashed_password": hashed_password,
                "role": role,
                "created_at": created_at,
                "quota_limits": quota_limits,
            }

    def update(self, user_id: UUID | str, **updates: Any) -> dict[str, Any]:
        """Update user fields."""
        with self._lock:
            user_id_str = str(user_id) if isinstance(user_id, UUID) else user_id

            if self._is_sqlite:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id_str,))
                if cursor.fetchone() is None:
                    raise ValueError(f"User {user_id_str} not found")
            elif self._is_mysql:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id_str,))
                if cursor.fetchone() is None:
                    raise ValueError(f"User {user_id_str} not found")
            else:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id_str,))
                    if cur.fetchone() is None:
                        raise ValueError(f"User {user_id_str} not found")

            if "email" in updates:
                new_email = updates["email"]
                if self._is_sqlite:
                    cursor = self._conn.cursor()
                    cursor.execute("SELECT user_id FROM users WHERE email = ? AND user_id != ?", (new_email, user_id_str))
                    if cursor.fetchone() is not None:
                        raise ValueError(f"Email {new_email} already registered")
                elif self._is_mysql:
                    cursor = self._conn.cursor()
                    cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (new_email, user_id_str))
                    if cursor.fetchone() is not None:
                        raise ValueError(f"Email {new_email} already registered")
                else:
                    with self._conn.cursor() as cur:
                        cur.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (new_email, user_id_str))
                        if cur.fetchone() is not None:
                            raise ValueError(f"Email {new_email} already registered")

            set_clauses = []
            params = []

            for key, value in updates.items():
                if key == "email":
                    set_clauses.append(f"email = {self._placeholder()}")
                elif key == "role":
                    set_clauses.append(f"role = {self._placeholder()}")
                    value = value.value
                elif key == "quota_limits":
                    set_clauses.append(f"quota_limits = {self._placeholder()}")
                    if not self._is_sqlite and not self._is_mysql:
                        value = f"{json.dumps(value)}::JSONB"
                    else:
                        value = json.dumps(value)
                params.append(value)

            if not set_clauses:
                row = self._get_row_by_id(user_id_str)
                return self._row_to_dict(row)

            params.append(user_id_str)

            if self._is_sqlite:
                query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
                cursor = self._conn.cursor()
                cursor.execute(query, params)
                self._conn.commit()
            elif self._is_mysql:
                query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = %s"
                cursor = self._conn.cursor()
                cursor.execute(query, params)
                self._conn.commit()
            else:
                query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = %s"
                with self._conn.cursor() as cur:
                    cur.execute(query, params)
                    self._conn.commit()

            row = self._get_row_by_id(user_id_str)
            if row is None:
                raise ValueError(f"User {user_id_str} not found after update")
            return self._row_to_dict(row)

    def _get_row_by_id(self, user_id_str: str) -> Any:
        """Internal method to get raw row by ID."""
        if self._is_sqlite:
            cursor = self._conn.cursor()
            cursor.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE user_id = ?", (user_id_str,))
            return cursor.fetchone()
        elif self._is_mysql:
            cursor = self._conn.cursor()
            cursor.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE user_id = %s", (user_id_str,))
            return cursor.fetchone()
        else:
            with self._conn.cursor() as cur:
                cur.execute("SELECT user_id, email, hashed_password, role, created_at, quota_limits FROM users WHERE user_id = %s", (user_id_str,))
                return cur.fetchone()

    def delete(self, user_id: UUID | str) -> None:
        """Delete a user."""
        with self._lock:
            user_id_str = str(user_id) if isinstance(user_id, UUID) else user_id

            if self._is_sqlite:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id_str,))
                if cursor.fetchone() is None:
                    raise ValueError(f"User {user_id_str} not found")
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id_str,))
                self._conn.commit()
            elif self._is_mysql:
                cursor = self._conn.cursor()
                cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id_str,))
                if cursor.fetchone() is None:
                    raise ValueError(f"User {user_id_str} not found")
                cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id_str,))
                self._conn.commit()
            else:
                with self._conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id_str,))
                    if cur.fetchone() is None:
                        raise ValueError(f"User {user_id_str} not found")
                    cur.execute("DELETE FROM users WHERE user_id = %s", (user_id_str,))
                    self._conn.commit()

    def list_users(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List all users with pagination."""
        with self._lock:
            if self._is_sqlite:
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    SELECT user_id, email, hashed_password, role, created_at, quota_limits
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )
                rows = cursor.fetchall()
            elif self._is_mysql:
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    SELECT user_id, email, hashed_password, role, created_at, quota_limits
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
                rows = cursor.fetchall()
            else:
                with self._conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT user_id, email, hashed_password, role, created_at, quota_limits
                        FROM users
                        ORDER BY created_at DESC
                        LIMIT %s OFFSET %s
                        """,
                        (limit, offset),
                    )
                    rows = cur.fetchall()

            return [self._row_to_dict(row) for row in rows]

    def _placeholder(self) -> str:
        """Get the appropriate placeholder for the current database backend."""
        return "?" if self._is_sqlite else "%s"

    def _row_to_dict(self, row: Any) -> dict[str, Any]:
        """Convert a database row to a user dict."""
        if self._is_mysql:
            # MySQL DictCursor returns dict directly
            user_id = row.get("user_id")
            email = row.get("email")
            hashed_password = row.get("hashed_password")
            role_str = row.get("role")
            created_at = row.get("created_at")
            quota_limits = row.get("quota_limits")
            if quota_limits is None:
                quota_limits = {}
            elif isinstance(quota_limits, str):
                quota_limits = json.loads(quota_limits)
        elif self._is_sqlite:
            user_id, email, hashed_password, role_str, created_at, quota_json = row
            if quota_json:
                quota_limits = json.loads(quota_json)
            else:
                quota_limits = {}
        else:
            user_id, email, hashed_password, role_str, created_at, quota_limits = row
            if quota_limits is None:
                quota_limits = {}

        try:
            role = UserRole(role_str)
        except ValueError:
            role = UserRole.USER

        return {
            "user_id": user_id,
            "email": email,
            "hashed_password": hashed_password,
            "role": role,
            "created_at": created_at,
            "quota_limits": quota_limits,
        }

    def _get_default_quotas(self, role: UserRole) -> dict[str, int]:
        """Get default quota limits for a role."""
        defaults = {
            UserRole.USER: {
                "max_threads": 10,
                "max_sandboxes": 5,
                "max_storage_mb": 1024,
            },
            UserRole.ADMIN: {
                "max_threads": 1000,
                "max_sandboxes": 500,
                "max_storage_mb": 102400,
            },
        }
        return defaults.get(role, defaults[UserRole.USER])

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self, "_pool") and self._pool is not None:
            try:
                self._pool.putconn(self._conn)
            except Exception:
                pass
        elif self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
