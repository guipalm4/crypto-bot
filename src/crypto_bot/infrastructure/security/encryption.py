"""
Encryption Service

Provides AES-256 encryption/decryption for sensitive data.
"""

import base64
import os
import warnings

from cryptography.fernet import Fernet, InvalidToken
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

        # Derive primary key
        self._primary_kid = "v1"
        self._fernet = self._create_fernet(encryption_key)

        # Optionally support previous key for smooth rotation
        previous_key = os.getenv("ENCRYPTION_KEY_PREVIOUS", "").strip()
        self._previous_kid = "v0" if previous_key else None
        self._fernet_previous = (
            self._create_fernet(previous_key) if previous_key else None
        )

    def _create_fernet(self, key: str) -> Fernet:
        """
        Create Fernet instance with derived key.

        Args:
            key: Base key string

        Returns:
            Fernet instance
        """
        # Use PBKDF2 to derive a proper key
        salt = os.getenv("ENCRYPTION_SALT", "crypto_bot_salt").encode()
        if salt == b"crypto_bot_salt":
            # Only warn in non-test environments (tests use default salt intentionally)
            if not os.getenv("PYTEST_CURRENT_TEST"):
                warnings.warn(
                    "Using default encryption salt. Set ENCRYPTION_SALT for improved security.",
                    RuntimeWarning,
                    stacklevel=2,
                )
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
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
        # Prefix with key id to support future rotations
        return f"{self._primary_kid}:{encrypted_bytes.decode()}"

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

        token = ciphertext
        # Detect key id prefix
        if ":" in ciphertext[:5]:
            kid, token = ciphertext.split(":", 1)
            if kid == self._primary_kid:
                decrypted_bytes = self._fernet.decrypt(token.encode())
                return decrypted_bytes.decode()
            if (
                self._previous_kid
                and kid == self._previous_kid
                and self._fernet_previous
            ):
                decrypted_bytes = self._fernet_previous.decrypt(token.encode())
                return decrypted_bytes.decode()
            # Unknown key id: fall through to try both
        # Backward compatibility: try current then previous
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except InvalidToken:
            if self._fernet_previous is None:
                raise
            return self._fernet_previous.decrypt(token.encode()).decode()


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
