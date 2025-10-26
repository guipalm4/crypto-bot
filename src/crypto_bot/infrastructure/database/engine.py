"""
Database Engine Configuration

This module provides async SQLAlchemy engine configuration using asyncpg.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from crypto_bot.config.settings import settings


class DatabaseEngine:
    """Async database engine manager."""

    def __init__(self) -> None:
        """Initialize database engine."""
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def create_engine(self) -> AsyncEngine:
        """Create async database engine with asyncpg driver."""
        if self._engine is None:
            # Convert postgresql:// to postgresql+asyncpg://
            database_url = settings.database_url
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )

            self._engine = create_async_engine(
                database_url,
                echo=settings.debug,
                future=True,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )
        return self._engine

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get async session factory."""
        if self._session_factory is None:
            engine = self.create_engine()
            self._session_factory = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return self._session_factory

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session.

        Yields:
            AsyncSession: Database session
        """
        session_factory = self.get_session_factory()
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    async def close(self) -> None:
        """Close database engine and connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


# Global database engine instance
db_engine = DatabaseEngine()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.

    Usage:
        async with get_db_session() as session:
            # Use session here
            ...

    Yields:
        AsyncSession: Database session
    """
    async for session in db_engine.get_session():
        yield session
