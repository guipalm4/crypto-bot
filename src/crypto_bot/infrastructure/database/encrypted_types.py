"""
Encrypted SQLAlchemy Types

Custom column types that automatically encrypt/decrypt data.
"""

from typing import Any

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from crypto_bot.infrastructure.security.encryption import get_encryption_service


class EncryptedString(TypeDecorator[str]):
    """
    SQLAlchemy type for encrypted strings.
    
    Automatically encrypts data before storing in database and
    decrypts when retrieving.
    """
    
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value: str | None, dialect: Any) -> str | None:
        """
        Encrypt string before storing in database.
        
        Args:
            value: Plaintext string
            dialect: SQLAlchemy dialect
        
        Returns:
            Encrypted string
        """
        if value is None:
            return None
        
        if not value:  # Empty string
            return ""
        
        encryption_service = get_encryption_service()
        return encryption_service.encrypt(value)
    
    def process_result_value(self, value: str | None, dialect: Any) -> str | None:
        """
        Decrypt string from database.
        
        Args:
            value: Encrypted string
            dialect: SQLAlchemy dialect
        
        Returns:
            Plaintext string
        """
        if value is None:
            return None
        
        if not value:  # Empty string
            return ""
        
        encryption_service = get_encryption_service()
        return encryption_service.decrypt(value)

