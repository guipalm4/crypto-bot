import os

import pytest

from crypto_bot.infrastructure.security.encryption import EncryptionService


@pytest.mark.unit
def test_encryption_with_key_prefix_and_rotation(monkeypatch):
    # Current key
    current_key = "current_key_123"
    # Previous key
    prev_key = "prev_key_abc"

    # Configure environment for rotation
    monkeypatch.setenv("ENCRYPTION_SALT", "testsalt")
    monkeypatch.setenv("ENCRYPTION_KEY_PREVIOUS", prev_key)

    svc = EncryptionService(current_key)

    # Encrypt with current key
    token = svc.encrypt("secret")
    assert token.startswith("v1:"), "token should include key-id prefix v1:"

    # Decrypt with current key
    assert svc.decrypt(token) == "secret"

    # Generate token as if written with previous key (v0:)
    prev_svc = EncryptionService(prev_key)
    prev_token = prev_svc.encrypt("oldsecret")
    prev_token = prev_token.replace("v1:", "v0:", 1)

    # Decrypt via rotation aware service
    assert svc.decrypt(prev_token) == "oldsecret"
