"""
Enhanced tests for logger redaction functionality.

Tests that verify expanded sensitive pattern redaction in logs.
"""

import logging
from io import StringIO

import pytest

from crypto_bot.utils.logger import REDACT_PATTERNS, get_logger


class TestLoggerRedaction:
    """Test suite for logger redaction of sensitive data."""

    def test_redacts_api_keys(self) -> None:
        """Test that API keys are redacted in logs."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("api_key=abc123xyz")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "abc123xyz" not in output

    def test_redacts_api_secrets(self) -> None:
        """Test that API secrets are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("api_secret=secret123 token=token456")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "secret123" not in output
        assert "token456" not in output

    def test_redacts_passphrases(self) -> None:
        """Test that passphrases are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("passphrase=TopSecret123")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "TopSecret123" not in output

    def test_redacts_passwords(self) -> None:
        """Test that passwords are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("password=mypassword123")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "mypassword123" not in output

    def test_redacts_postgres_passwords(self) -> None:
        """Test that PostgreSQL passwords are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("postgres_password=dbpass123")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "dbpass123" not in output

    def test_redacts_jwt_secrets(self) -> None:
        """Test that JWT secrets are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("jwt_secret=secretjwt123")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "secretjwt123" not in output

    def test_redacts_encryption_keys(self) -> None:
        """Test that encryption keys are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("encryption_key=key123456")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "key123456" not in output

    def test_redacts_telegram_tokens(self) -> None:
        """Test that Telegram bot tokens are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("telegram_bot_token=123456:ABC-DEF1234ghIkl")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "123456:ABC-DEF1234ghIkl" not in output

    def test_redacts_discord_webhooks(self) -> None:
        """Test that Discord webhook URLs are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("discord_webhook=https://discord.com/api/webhooks/123/token")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "discord.com/api/webhooks" not in output or "/123/token" not in output

    def test_redacts_smtp_passwords(self) -> None:
        """Test that SMTP passwords are redacted."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("smtp_password=emailpass123")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "emailpass123" not in output

    def test_case_insensitive_redaction(self) -> None:
        """Test that redaction is case-insensitive."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("API_KEY=abc123 PASSWORD=pass456")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "abc123" not in output
        assert "pass456" not in output

    def test_multiple_secrets_in_single_message(self) -> None:
        """Test redaction of multiple secrets in one log message."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("Connecting: api_key=key1 secret=secret1 token=tok1 password=pass1")
        output = stream.getvalue()

        assert "[REDACTED]" in output
        assert "key1" not in output
        assert "secret1" not in output
        assert "tok1" not in output
        assert "pass1" not in output

    def test_non_sensitive_data_preserved(self) -> None:
        """Test that non-sensitive data is preserved."""
        stream = StringIO()
        logger = get_logger("test")

        for h in logger.handlers:
            if isinstance(h, logging.StreamHandler):
                h.stream = stream

        logger.info("User john_doe connected with status=active")
        output = stream.getvalue()

        assert "john_doe" in output
        assert "status=active" in output


class TestRedactionPatterns:
    """Test individual redaction patterns."""

    def test_all_patterns_compiled(self) -> None:
        """Verify all redaction patterns are valid regex."""
        assert len(REDACT_PATTERNS) > 0
        for pattern in REDACT_PATTERNS:
            # Test pattern doesn't crash on compilation
            assert pattern.pattern is not None

    def test_pattern_covers_exchange_creds(self) -> None:
        """Verify exchange credential patterns work."""
        test_string = "api_key=test123 api_secret=secret456 passphrase=pass789"
        result = test_string

        # Apply all patterns
        for pattern in REDACT_PATTERNS:
            result = pattern.sub(r"\1[REDACTED]", result)

        # Verify sensitive values are redacted
        assert "[REDACTED]" in result
        assert "test123" not in result
        assert "secret456" not in result
        assert "pass789" not in result
