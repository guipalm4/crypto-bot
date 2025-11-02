"""
Pytest configuration and shared fixtures for manual QA tests.

This module provides fixtures and utilities specific to manual QA tests
that were created from validated manual test scenarios.
"""

import os
from typing import AsyncGenerator

import pytest

# Set test encryption key BEFORE importing any application modules
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_long!!"


@pytest.fixture(scope="function")
def manual_qa_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Setup environment for manual QA tests.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    # Ensure encryption key is set
    monkeypatch.setenv("ENCRYPTION_KEY", "test_encryption_key_32_bytes_long!!")
    monkeypatch.setenv("ENCRYPTION_SALT", "test_salt_16_bytes")

    # Disable real API calls in tests (use mocks)
    monkeypatch.setenv("BINANCE_SANDBOX", "true")
    monkeypatch.setenv("COINBASE_SANDBOX", "true")


@pytest.fixture
async def clean_test_environment() -> AsyncGenerator[None, None]:
    """
    Provide a clean test environment for each test.

    This fixture ensures test isolation by cleaning up any state
    between test runs.

    Yields:
        None
    """
    # Setup
    yield
    # Cleanup (if needed)


# Pytest configuration
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest markers for manual QA tests."""
    config.addinivalue_line(
        "markers",
        "manual_qa: Tests created from validated manual QA scenarios",
    )
    config.addinivalue_line(
        "markers",
        "qa_cli: CLI-related manual QA tests",
    )
    config.addinivalue_line(
        "markers",
        "qa_exchange: Exchange integration manual QA tests",
    )
    config.addinivalue_line(
        "markers",
        "qa_strategy: Strategy plugin manual QA tests",
    )
    config.addinivalue_line(
        "markers",
        "qa_risk: Risk management manual QA tests",
    )
    config.addinivalue_line(
        "markers",
        "qa_config: Configuration and persistence manual QA tests",
    )
    config.addinivalue_line(
        "markers",
        "qa_security: Security and encryption manual QA tests",
    )
    config.addinivalue_line(
        "markers",
        "qa_exploratory: Exploratory and edge case manual QA tests",
    )
