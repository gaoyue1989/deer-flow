"""Async checkpointer factory.

Provides an **async context manager** for long-running async servers that need
proper resource cleanup.

Supported backends: memory, sqlite, postgres.

Usage (e.g. FastAPI lifespan)::

    from deerflow.agents.checkpointer.async_provider import make_checkpointer

    async with make_checkpointer() as checkpointer:
        app.state.checkpointer = checkpointer  # InMemorySaver if not configured

For sync usage see :mod:`deerflow.agents.checkpointer.provider`.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from langgraph.types import Checkpointer

from deerflow.agents.checkpointer.provider import (
    MYSQL_CONN_REQUIRED,
    MYSQL_INSTALL,
    POSTGRES_CONN_REQUIRED,
    POSTGRES_INSTALL,
    SQLITE_INSTALL,
)
from deerflow.config.app_config import get_app_config
from deerflow.runtime.store._sqlite_utils import ensure_sqlite_parent_dir, resolve_sqlite_conn_str

logger = logging.getLogger(__name__)


class _PooledMySQLCheckpointer:
    """Wrapper around AIOMySQLSaver backed by an aiomysql connection pool.

    Uses a connection pool instead of a single long-lived connection to:
    - Automatically handle MySQL server idle timeouts (wait_timeout)
    - Support concurrent checkpointer operations without lock contention
    - Transparently replace stale connections from the pool
    """

    def __init__(self, conn_string: str, *, minsize: int = 1, maxsize: int = 5, serde=None):
        self._conn_string = conn_string
        self._minsize = minsize
        self._maxsize = maxsize
        self._serde = serde
        self._pool = None
        self._saver = None

    async def _create_pool(self):
        """Create the aiomysql connection pool."""
        import aiomysql
        from langgraph.checkpoint.mysql.aio import AIOMySQLSaver

        params = AIOMySQLSaver.parse_conn_string(self._conn_string)
        self._pool = await aiomysql.create_pool(
            host=params["host"],
            user=params["user"],
            password=params["password"],
            db=params["db"],
            port=params["port"],
            minsize=self._minsize,
            maxsize=self._maxsize,
            autocommit=True,
            pool_recycle=3600,  # Recycle connections every hour
        )
        logger.info("MySQL connection pool created (min=%d, max=%d)", self._minsize, self._maxsize)

    async def _get_saver(self):
        """Get or create the AIOMySQLSaver backed by the pool."""
        if self._saver is None:
            from langgraph.checkpoint.mysql.aio import AIOMySQLSaver

            self._saver = AIOMySQLSaver(conn=self._pool, serde=self._serde)
            await self._saver.setup()
            logger.info("MySQL checkpointer initialized with connection pool")
        return self._saver

    # Checkpointer interface — delegate to the saver
    async def alist(self, *args, **kwargs):
        saver = await self._get_saver()
        async for item in saver.alist(*args, **kwargs):
            yield item

    async def aget_tuple(self, *args, **kwargs):
        saver = await self._get_saver()
        return await saver.aget_tuple(*args, **kwargs)

    async def aget(self, *args, **kwargs):
        saver = await self._get_saver()
        return await saver.aget(*args, **kwargs)

    async def aput(self, *args, **kwargs):
        saver = await self._get_saver()
        return await saver.aput(*args, **kwargs)

    async def aput_writes(self, *args, **kwargs):
        saver = await self._get_saver()
        return await saver.aput_writes(*args, **kwargs)

    async def adelete_thread(self, *args, **kwargs):
        saver = await self._get_saver()
        return await saver.adelete_thread(*args, **kwargs)

    def get_next_version(self, *args, **kwargs):
        """Synchronous method — delegate to the saver's sync version."""
        # Note: _get_saver is async, but get_next_version is sync.
        # We need to access _saver directly, assuming it's already initialized.
        if self._saver is None:
            raise RuntimeError("Checkpointer not initialized. Call _get_saver first.")
        return self._saver.get_next_version(*args, **kwargs)

    async def close(self):
        """Close the connection pool."""
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            logger.info("MySQL connection pool closed")
            self._pool = None
            self._saver = None


# ---------------------------------------------------------------------------
# Async factory
# ---------------------------------------------------------------------------


@contextlib.asynccontextmanager
async def _async_checkpointer(config) -> AsyncIterator[Checkpointer]:
    """Async context manager that constructs and tears down a checkpointer."""
    if config.type == "memory":
        from langgraph.checkpoint.memory import InMemorySaver

        yield InMemorySaver()
        return

    if config.type == "sqlite":
        try:
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        except ImportError as exc:
            raise ImportError(SQLITE_INSTALL) from exc

        conn_str = resolve_sqlite_conn_str(config.connection_string or "store.db")
        await asyncio.to_thread(ensure_sqlite_parent_dir, conn_str)
        async with AsyncSqliteSaver.from_conn_string(conn_str) as saver:
            await saver.setup()
            yield saver
        return

    if config.type == "postgres":
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        except ImportError as exc:
            raise ImportError(POSTGRES_INSTALL) from exc

        if not config.connection_string:
            raise ValueError(POSTGRES_CONN_REQUIRED)

        async with AsyncPostgresSaver.from_conn_string(config.connection_string) as saver:
            await saver.setup()
            yield saver
        return

    if config.type == "mysql":
        try:
            from langgraph.checkpoint.mysql.aio import AIOMySQLSaver  # noqa: F401
        except ImportError as exc:
            raise ImportError(MYSQL_INSTALL) from exc

        if not config.connection_string:
            raise ValueError(MYSQL_CONN_REQUIRED)

        saver = _PooledMySQLCheckpointer(config.connection_string)
        await saver._create_pool()
        await saver._get_saver()
        logger.info("Checkpointer: using AIOMySQLSaver with connection pool")
        try:
            yield saver
        finally:
            await saver.close()
        return

    raise ValueError(f"Unknown checkpointer type: {config.type!r}")


# ---------------------------------------------------------------------------
# Public async context manager
# ---------------------------------------------------------------------------


@contextlib.asynccontextmanager
async def make_checkpointer() -> AsyncIterator[Checkpointer]:
    """Async context manager that yields a checkpointer for the caller's lifetime.
    Resources are opened on enter and closed on exit — no global state::

        async with make_checkpointer() as checkpointer:
            app.state.checkpointer = checkpointer

    Yields an ``InMemorySaver`` when no checkpointer is configured in *config.yaml*.
    """

    config = get_app_config()

    if config.checkpointer is None:
        from langgraph.checkpoint.memory import InMemorySaver

        yield InMemorySaver()
        return

    async with _async_checkpointer(config.checkpointer) as saver:
        yield saver
