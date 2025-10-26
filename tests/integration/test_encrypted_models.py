"""
Integration tests for encrypted database fields.
"""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from crypto_bot.infrastructure.database import Base, db_engine
from crypto_bot.infrastructure.database.models import Exchange
from crypto_bot.infrastructure.security.encryption import initialize_encryption_service


@pytest.fixture(scope="module")
def setup_encryption() -> None:
    """Initialize encryption service for tests."""
    initialize_encryption_service("test_encryption_key_12345")


@pytest.fixture
async def setup_database(setup_encryption: None) -> None:
    """Set up test database schema."""
    engine = db_engine.create_engine()

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await db_engine.close()


@pytest.fixture
async def db_session(setup_database: None) -> AsyncSession:
    """Get database session for tests."""
    session_factory = db_engine.get_session_factory()
    async with session_factory() as session:
        yield session


@pytest.mark.integration
@pytest.mark.asyncio
async def test_store_encrypted_credentials(db_session: AsyncSession) -> None:
    """Test that API credentials are encrypted when stored."""
    # Create exchange with API credentials
    exchange = Exchange(
        name="binance_test",
        api_key_encrypted="my_secret_api_key",
        api_secret_encrypted="my_secret_api_secret",
        is_active=True,
    )

    db_session.add(exchange)
    await db_session.commit()
    await db_session.refresh(exchange)

    # In application code, credentials should be decrypted automatically
    assert exchange.api_key_encrypted == "my_secret_api_key"
    assert exchange.api_secret_encrypted == "my_secret_api_secret"

    # But in database, they should be encrypted (different from plaintext)
    result = await db_session.execute(
        text(
            "SELECT api_key_encrypted, api_secret_encrypted "
            "FROM exchange WHERE name = :name"
        ),
        {"name": "binance_test"},
    )
    row = result.fetchone()

    # Database values should be encrypted (not equal to plaintext)
    assert row[0] != "my_secret_api_key"
    assert row[1] != "my_secret_api_secret"

    # And should not be empty
    assert row[0] is not None
    assert row[1] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retrieve_decrypted_credentials(db_session: AsyncSession) -> None:
    """Test that credentials are automatically decrypted when retrieved."""
    # Store exchange
    exchange = Exchange(
        name="coinbase_test",
        api_key_encrypted="test_api_key",
        api_secret_encrypted="test_api_secret",
    )

    db_session.add(exchange)
    await db_session.commit()

    exchange_id = exchange.id

    # Clear session to force database read
    await db_session.close()

    # Retrieve exchange
    session_factory = db_engine.get_session_factory()
    async with session_factory() as new_session:
        result = await new_session.execute(
            select(Exchange).where(Exchange.id == exchange_id)
        )
        retrieved_exchange = result.scalar_one()

        # Credentials should be automatically decrypted
        assert retrieved_exchange.api_key_encrypted == "test_api_key"
        assert retrieved_exchange.api_secret_encrypted == "test_api_secret"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_encrypted_credentials(db_session: AsyncSession) -> None:
    """Test updating encrypted credentials."""
    # Create exchange
    exchange = Exchange(
        name="kraken_test",
        api_key_encrypted="old_key",
        api_secret_encrypted="old_secret",
    )

    db_session.add(exchange)
    await db_session.commit()

    # Update credentials
    exchange.api_key_encrypted = "new_key"
    exchange.api_secret_encrypted = "new_secret"
    await db_session.commit()
    await db_session.refresh(exchange)

    # Verify updated values
    assert exchange.api_key_encrypted == "new_key"
    assert exchange.api_secret_encrypted == "new_secret"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_null_encrypted_fields(db_session: AsyncSession) -> None:
    """Test that null values work correctly with encrypted fields."""
    # Create exchange without credentials
    exchange = Exchange(
        name="no_credentials_test",
        api_key_encrypted=None,
        api_secret_encrypted=None,
    )

    db_session.add(exchange)
    await db_session.commit()
    await db_session.refresh(exchange)

    # Null values should remain null
    assert exchange.api_key_encrypted is None
    assert exchange.api_secret_encrypted is None
