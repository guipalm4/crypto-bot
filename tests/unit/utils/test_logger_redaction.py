import logging
from io import StringIO

from crypto_bot.utils.logger import get_logger


def test_logger_redacts_sensitive_values(monkeypatch):
    stream = StringIO()
    logger = get_logger("test.logger")

    # Replace handler stream to capture output
    for h in logger.handlers:
        if isinstance(h, logging.StreamHandler):
            h.stream = stream

    logger.info("api_key=abc123 secret=xyz passphrase=topsecret")
    out = stream.getvalue()
    assert "[REDACTED]" in out
    assert "abc123" not in out
    assert "xyz" not in out
