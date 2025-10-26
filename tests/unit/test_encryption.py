"""
Unit tests for encryption service.
"""

import pytest
from cryptography.fernet import InvalidToken

from crypto_bot.infrastructure.security.encryption import EncryptionService


class TestEncryptionService:
    """Tests for EncryptionService."""

    def test_create_encryption_service(self) -> None:
        """Test creating encryption service."""
        service = EncryptionService("test_key_12345")
        assert service is not None

    def test_encryption_service_requires_key(self) -> None:
        """Test that encryption service requires a key."""
        with pytest.raises(ValueError, match="Encryption key must be provided"):
            EncryptionService("")

    def test_encrypt_decrypt_string(self) -> None:
        """Test encrypting and decrypting a string."""
        service = EncryptionService("test_key_12345")

        plaintext = "my_secret_api_key"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert encrypted != plaintext  # Should be encrypted
        assert decrypted == plaintext  # Should decrypt back to original

    def test_encrypt_empty_string(self) -> None:
        """Test encrypting empty string."""
        service = EncryptionService("test_key_12345")

        encrypted = service.encrypt("")
        assert encrypted == ""

        decrypted = service.decrypt(encrypted)
        assert decrypted == ""

    def test_encrypted_data_is_different_each_time(self) -> None:
        """Test that encrypting same data produces different ciphertext each time."""
        service = EncryptionService("test_key_12345")

        plaintext = "my_secret_api_key"
        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)

        # Fernet includes timestamp and random data, so ciphertexts differ
        assert encrypted1 != encrypted2

        # But both decrypt to same plaintext
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext

    def test_decrypt_with_wrong_key_fails(self) -> None:
        """Test that decrypting with wrong key fails."""
        service1 = EncryptionService("key1")
        service2 = EncryptionService("key2")

        plaintext = "my_secret_api_key"
        encrypted = service1.encrypt(plaintext)

        # Decrypting with different key should fail
        with pytest.raises(InvalidToken):
            service2.decrypt(encrypted)

    def test_encrypt_unicode_characters(self) -> None:
        """Test encrypting unicode characters."""
        service = EncryptionService("test_key_12345")

        plaintext = "こんにちは世界 🔒🔑"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_long_string(self) -> None:
        """Test encrypting long string."""
        service = EncryptionService("test_key_12345")

        plaintext = "a" * 10000
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext
