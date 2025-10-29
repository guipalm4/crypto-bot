"""
Tests for system events logging.
"""

import json
import logging
import sys
from io import StringIO

import pytest

from crypto_bot.utils.structured_logger import configure_structlog
from crypto_bot.utils.system_events import (
    log_config_change,
    log_critical_error,
    log_error,
    log_exception_with_context,
    log_shutdown,
    log_startup,
    log_system_event,
)


class TestSystemEvents:
    """Test suite for system events logging."""

    def setup_method(self) -> None:
        """Initialize logging before each test."""
        # Reset logging configuration
        logging.getLogger().handlers.clear()
        configure_structlog(level="INFO", format="json", output="console")

    def test_log_startup(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test logging application startup."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        log_startup(
            app_name="TestApp",
            version="1.0.0",
            environment="test",
            extra_field="value",
        )

        captured = capsys.readouterr()
        output_lines = [
            line.strip() for line in captured.out.strip().split("\n") if line.strip()
        ]

        if output_lines:
            parsed = json.loads(output_lines[-1])
            assert parsed["event"] == "application_startup"
            assert parsed["app_name"] == "TestApp"
            assert parsed["version"] == "1.0.0"
            assert parsed["environment"] == "test"
            assert parsed["event_type"] == "system_lifecycle"

    def test_log_shutdown(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test logging application shutdown."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        log_shutdown(reason="test_shutdown", exit_code=0)

        captured = capsys.readouterr()
        output_lines = [
            line.strip() for line in captured.out.strip().split("\n") if line.strip()
        ]

        if output_lines:
            parsed = json.loads(output_lines[-1])
            assert parsed["event"] == "application_shutdown"
            assert parsed["reason"] == "test_shutdown"
            assert parsed["exit_code"] == 0
            assert parsed["event_type"] == "system_lifecycle"

    def test_log_config_change(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test logging configuration changes."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        log_config_change(
            section="database",
            key="host",
            old_value="localhost",
            new_value="192.168.1.1",
        )

        captured = capsys.readouterr()
        output_lines = [
            line.strip() for line in captured.out.strip().split("\n") if line.strip()
        ]

        if output_lines:
            parsed = json.loads(output_lines[-1])
            assert parsed["event"] == "configuration_changed"
            assert parsed["section"] == "database"
            assert parsed["key"] == "host"
            assert parsed["old_value"] == "localhost"
            assert parsed["new_value"] == "192.168.1.1"
            assert parsed["event_type"] == "configuration"

    def test_log_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test logging errors with context."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.ERROR)

        error = ValueError("Test error message")
        log_error(error, context={"module": "test", "operation": "test_op"})

        captured = capsys.readouterr()
        output_lines = [
            line.strip() for line in captured.out.strip().split("\n") if line.strip()
        ]

        if output_lines:
            parsed = json.loads(output_lines[-1])
            assert parsed["event"] == "error_occurred"
            assert parsed["error_type"] == "ValueError"
            assert parsed["error_message"] == "Test error message"
            assert parsed["event_type"] == "error"
            assert parsed["module"] == "test"
            assert parsed["operation"] == "test_op"

    def test_log_critical_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test logging critical errors."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.CRITICAL)

        error = RuntimeError("Critical test error")
        log_critical_error(error, context={"component": "test"})

        captured = capsys.readouterr()
        output_lines = [
            line.strip() for line in captured.out.strip().split("\n") if line.strip()
        ]

        if output_lines:
            parsed = json.loads(output_lines[-1])
            assert parsed["event"] == "critical_error"
            assert parsed["error_type"] == "RuntimeError"
            assert parsed["event_type"] == "critical_error"

    def test_log_system_event(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test logging generic system events."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        log_system_event(
            "test_event",
            event_type="monitoring",
            metric="cpu_usage",
            value=85.5,
        )

        captured = capsys.readouterr()
        output_lines = [
            line.strip() for line in captured.out.strip().split("\n") if line.strip()
        ]

        if output_lines:
            parsed = json.loads(output_lines[-1])
            assert parsed["event"] == "test_event"
            assert parsed["event_type"] == "monitoring"
            assert parsed["metric"] == "cpu_usage"
            assert parsed["value"] == 85.5

    def test_log_exception_with_context(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test logging exception with specific logger context."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.ERROR)

        error = KeyError("missing_key")
        log_exception_with_context(
            "test.module",
            error,
            context={"key": "test_key"},
            level="error",
        )

        captured = capsys.readouterr()
        output_lines = [
            line.strip() for line in captured.out.strip().split("\n") if line.strip()
        ]

        if output_lines:
            parsed = json.loads(output_lines[-1])
            assert parsed["event"] == "exception_caught"
            assert parsed["error_type"] == "KeyError"
