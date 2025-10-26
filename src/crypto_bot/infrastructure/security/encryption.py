"""
Encryption Service

Provides AES-256 encryption/decryption for sensitive data.
"""

import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data using AES-256.

    Uses Fernet (symmetric encryption) which provides authenticated encryption
    with AES-128-CBC and HMAC.
    """

    def __init__(self, encryption_key: str) -> None:
        """
        Initialize encryption service.

        Args:
            encryption_key: Base encryption key (will be derived using PBKDF2)

        Raises:
            ValueError: If encryption key is not provided
        """
        if not encryption_key:
            raise ValueError("Encryption key must be provided")

        # Derive a proper key from the provided key using PBKDF2
        self._fernet = self._create_fernet(encryption_key)

    def _create_fernet(self, key: str) -> Fernet:
        """
        Create Fernet instance with derived key.

        Args:
            key: Base key string

        Returns:
            Fernet instance
        """
        # Use PBKDF2 to derive a proper key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"crypto_bot_salt",  # In production, use a random salt stored securely
            iterations=100000,
            backend=default_backend(),
        )

        derived_key = base64.urlsafe_b64encode(kdf.derive(key.encode()))
        return Fernet(derived_key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return ""

        encrypted_bytes = self._fernet.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            Decrypted plaintext string

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        if not ciphertext:
            return ""

        decrypted_bytes = self._fernet.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()


# Global encryption service instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """
    Get global encryption service instance.

    Returns:
        EncryptionService instance

    Raises:
        RuntimeError: If encryption service not initialized
    """
    global _encryption_service

    if _encryption_service is None:
        from crypto_bot.config.settings import settings

        if not settings.encryption_key:
            raise RuntimeError(
                "Encryption key not configured. "
                "Set ENCRYPTION_KEY environment variable."
            )

        _encryption_service = EncryptionService(settings.encryption_key)

    return _encryption_service


def initialize_encryption_service(encryption_key: str) -> None:
    """
    Initialize global encryption service.

    Args:
        encryption_key: Encryption key
    """
    global _encryption_service
    _encryption_service = EncryptionService(encryption_key)
