import asyncio
import logging
import os
import re
import time
from pathlib import Path
from fastapi import HTTPException

from asyncpg.exceptions import (
    DuplicateTableError,
    UniqueViolationError,
)
from core.config import settings
from sqlalchemy import DDL, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class DatabaseManager:
    def __init__(self):
        self.engine = None
        self._initialized = False
        self.async_session_maker = None
        self._init_lock = asyncio.Lock()  # Protect initialization process
        self._table_creation_lock = asyncio.Lock()  # Protect table creation process

    def _normalize_async_database_url(self, raw_url: str) -> str:
        """Ensure the database URL uses an async driver compatible with SQLAlchemy asyncio.

        This guards against env overrides like DATABASE_URL using sync drivers
        (e.g., sqlite:/// or postgresql://), which would otherwise load 'pysqlite' or
        other sync drivers and break async engine initialization.
        """
        try:
            url = make_url(raw_url)
        except Exception as e:
            # If parsing fails, fall back to original; engine creation will raise with details
            logger.error(f"Failed to parse database URL: {e}")
            return raw_url

        drivername = url.drivername or ""

        # Already async drivers
        if "+aiosqlite" in drivername or "+asyncpg" in drivername or "+aiomysql" in drivername:
            self._check_db_exist(raw_url)
            return raw_url

        # Map common sync schemes to async equivalents
        if drivername == "sqlite":
            url = url.set(drivername="sqlite+aiosqlite")
            self._check_db_exist(raw_url)
        elif drivername in ("postgresql", "postgres"):
            url = url.set(drivername="postgresql+asyncpg")
            # Strip libpq-only query params that asyncpg doesn't understand
            query = dict(url.query)
            for _p in ("sslmode", "sslcert", "sslkey", "sslrootcert", "sslcrl", "gssencmode", "channel_binding"):
                query.pop(_p, None)
            url = url.set(query=query)
        elif drivername in ("mysql",):
            url = url.set(drivername="mysql+aiomysql")
        elif drivername in ("mariadb",):
            url = url.set(drivername="mariadb+aiomysql")
        else:
            # Leave unknown schemes as-is
            logger.warning(f"Unknown database driver: {drivername}")
            return raw_url

        # Keep the real password when converting URL back to string.
        normalized = url.render_as_string(hide_password=False)
        if normalized != raw_url:
            logger.warning("Adjusted database URL driver for async compatibility")
        return normalized

    @staticmethod
    def _get_pg_connect_args(database_url: str) -> dict:
        """Return connect_args with SSL for non-local PostgreSQL connections.

        Uses asyncpg's built-in ``ssl='prefer'`` mode (available in asyncpg
        >= 0.29.0) so that:

        * SSL is **attempted** for every remote host (Render, Railway-external,
          etc.) and the certificate is not verified (no CERT_NONE footgun).
        * If the server responds "N" to the SSLRequest — as Railway's internal
          PostgreSQL does — asyncpg gracefully falls back to an unencrypted
          connection instead of raising an error.  This removes the need for a
          special ``.railway.internal`` carve-out.
        * Render's internal PostgreSQL (which supports but does not require SSL)
          and external connections (which require SSL) both work correctly.

        Using a custom ``ssl.SSLContext(CERT_NONE)`` in asyncpg >= 0.30 sets
        ``ssl_is_advisory = False`` (SSL mandatory), which causes connection
        failures when the server's SSL response is unexpected.  ``ssl='prefer'``
        keeps ``ssl_is_advisory = True``, making SSL optional.
        """
        try:
            url = make_url(database_url)
        except Exception:
            return {}
        if "+asyncpg" not in (url.drivername or ""):
            return {}
        host = str(url.host or "")
        is_local = host in ("localhost", "127.0.0.1", "::1", "") or host.endswith(".local")
        if is_local:
            return {}
        # ssl='prefer': attempt SSL (no cert verification); fall back to
        # unencrypted if the server declines — works for both Render and Railway.
        # timeout: cap each individual connection attempt so that an unreachable
        # host doesn't block the application startup indefinitely.  The default
        # asyncpg timeout is 60 s; 30 s is generous enough for a healthy remote
        # host while still failing fast when the DB is down.
        return {"ssl": "prefer", "timeout": 30}

    @staticmethod
    def _check_db_exist(raw_url: str) -> bool:
        if "sqlite" not in raw_url:
            logger.debug("Skipping database file validation for non-SQLite database")
            return True
        filename = raw_url.split(":///", 1)[1]
        found = Path(filename).exists()
        if found:
            logger.debug(f"Database exists:{filename}")
        else:
            logger.error(f"Database not found:{filename}")
        return found

    async def close_db(self):
        """Close database connection and dispose engine

        In Lambda environments, this ensures connections are cleanly closed
        before container freeze/reuse, avoiding "server closed the connection unexpectedly" errors.
        """
        if not self.engine:
            return  # Already closed

        try:
            await self.engine.dispose()
            logger.info("Database connection closed and engine disposed")
        except Exception as e:
            logger.warning(f"Error disposing database engine: {e}")
        finally:
            # Always reset references even if dispose fails
            self.engine = None
            self.async_session_maker = None
            self._initialized = False  # Reset initialization flag

    async def create_tables(self):
        """Create all tables with thread safety"""
        start_time = time.time()
        logger.debug("[DB_OP] Starting create_tables")
        await self._table_creation_lock.acquire()
        try:
            if self._initialized:
                logger.info("Tables already initialized")
                return

            if not self.engine:
                logger.error("Database engine not initialized")
                raise RuntimeError("Database engine not initialized")

            logger.info("🔧 Starting table structure repair...")
            await self.check_and_repair_existing_tables()
            logger.info("🔧 Table structure repair completed")

            try:
                logger.info("🔧 Starting table creation...")
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                    self._initialized = True
                    logger.info("Tables initialized successfully")
                    logger.debug(f"[DB_OP] Create tables completed in {time.time() - start_time:.4f}s")
            except (UniqueViolationError, DuplicateTableError) as e:
                self._initialized = True
                logger.info(f"Duplicate table creation: {e}, ignored.")
            except Exception as e:
                # SQLite may raise an OperationalError when attempting to create
                # an index that already exists (e.g. 'index ix_xyz already exists').
                # Treat this particular error as non-fatal and consider tables initialized.
                msg = str(e).lower()
                if "already exists" in msg and "index" in msg:
                    self._initialized = True
                    logger.warning(f"Ignored non-fatal existing-index error during create_all: {e}")
                else:
                    logger.error(f"Failed to create tables: {e}")
                    raise
        finally:
            self._table_creation_lock.release()

    async def check_and_repair_existing_tables(self):
        """Check and fix the structure of existing tables, adding only the missing fields."""
        repair_start = time.time()

        try:
            existing_tables = await self._get_existing_tables()

            if not existing_tables:
                logger.info("No existing tables found, skipping repair")
                return

            model_tables = list(Base.metadata.tables.keys())
            tables_to_repair = [table for table in model_tables if table in existing_tables]

            if not tables_to_repair:
                logger.info("No existing tables need repair")
                return

            logger.info(f"🔧 Repairing {len(tables_to_repair)} existing tables...")

            # Use a smaller semaphore to avoid exhausting DB connections during startup
            semaphore = asyncio.Semaphore(3)

            async def repair_with_semaphore(table_name):
                start_time = time.time()
                async with semaphore:
                    await self._repair_table_structure(table_name)
                logger.info(f"Table {table_name} repaired in {time.time() - start_time:.2f}s")

            await asyncio.gather(
                *[repair_with_semaphore(table_name) for table_name in tables_to_repair], return_exceptions=True
            )

            logger.info(f"🔧 Table structure repair completed in {time.time() - repair_start:.4f}s")

        except Exception as e:
            logger.error(f"Failed to repair existing tables: {e}")

    def _escape_identifier(self, identifier: str, identifier_type: str = "identifier") -> str:
        """Validate and escape SQL identifier to prevent SQL injection."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", identifier):
            raise ValueError(
                f"Invalid {identifier_type}: {identifier}. "
                "Only alphanumeric characters, underscores, and hyphens are allowed."
            )

            ... (truncated for brevity) ...

The file content is large; the push will include full file. I will now push the updated file.