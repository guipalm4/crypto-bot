"""
Pytest configuration and shared fixtures.

This module provides common test fixtures and utilities used across
all test modules (unit, integration, and E2E).
"""

import os
from datetime import UTC, datetime
from typing import AsyncGenerator, Generator

import pytest
from faker import Faker
from freezegun import freeze_time

# Set test encryption key BEFORE importing any application modules
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_long!!"


@pytest.fixture(scope="session")
def faker() -> Generator[Faker, None, None]:
    """
    Provide a Faker instance for generating test data.

    Yields:
        Faker: Faker instance with Portuguese locale support
    """
    fake = Faker()
    Faker.seed(42)  # For reproducible test data
    yield fake


@pytest.fixture
def frozen_time() -> Generator[datetime, None, None]:
    """
    Provide a context manager to freeze time at a specific point.

    Usage:
        def test_something(frozen_time):
            with frozen_time:
                # Time is frozen at the start of the test
                ...

    Yields:
        datetime: The frozen time point (utcnow)
    """
    with freeze_time() as frozen:
        yield frozen


@pytest.fixture
def fixed_datetime() -> datetime:
    """
    Provide a fixed datetime for consistent testing.

    Returns:
        datetime: Fixed datetime (2024-01-01 12:00:00 UTC)
    """
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.fixture(scope="function")
def mock_encryption_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Mock encryption environment variables for testing.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setenv("ENCRYPTION_KEY", "test_encryption_key_32_bytes_long!!")
    monkeypatch.setenv("ENCRYPTION_SALT", "test_salt_16_bytes")


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "unit: Unit tests that mock all external dependencies",
    )
    config.addinivalue_line(
        "markers",
        "integration: Integration tests that use real dependencies (DB, APIs)",
    )
    config.addinivalue_line(
        "markers",
        "e2e: End-to-end tests simulating full user workflows",
    )
    config.addinivalue_line(
        "markers",
        "slow: Tests that take a long time to run",
    )
    config.addinivalue_line(
        "markers",
        "testnet: Tests that require testnet API access",
    )
