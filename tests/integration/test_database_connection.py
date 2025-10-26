"""
Integration tests for database connection.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.infrastructure.database import db_engine, get_db_session


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection() -> None:
    """Test that async database connection can be established and closed."""
    # Create engine
    engine = db_engine.create_engine()
    assert engine is not None

    # Test connection
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

    # Close engine
    await db_engine.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_factory() -> None:
    """Test that session factory can be created and sessions work correctly."""
    session_factory = db_engine.get_session_factory()
    assert session_factory is not None

    async with session_factory() as session:
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    await db_engine.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_db_session_dependency() -> None:
    """Test the get_db_session dependency function."""
    async for session in get_db_session():
        assert isinstance(session, AsyncSession)
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    await db_engine.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_sessions() -> None:
    """Test that multiple sessions can be created and used concurrently."""
    sessions = []

    # Create multiple sessions
    for _ in range(3):
        async for session in get_db_session():
            sessions.append(session)
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    assert len(sessions) == 3
    await db_engine.close()
