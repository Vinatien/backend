"""Encryption utilities for sensitive data."""

from cryptography.fernet import Fernet
from typing import Optional


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""

    _instance = None
    _cipher = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_cipher(self):
        """Lazy-load cipher on first use."""
        if self._cipher is None:
            from app.utils.settings import ENCRYPTION_KEY
            if not ENCRYPTION_KEY:
                raise ValueError("ENCRYPTION_KEY must be set in environment variables")
            self._cipher = Fernet(ENCRYPTION_KEY.encode())
        return self._cipher

    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string, or None if input is None
        """
        if plaintext is None:
            return None
        return self._get_cipher().encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: Optional[str]) -> Optional[str]:
        """
        Decrypt encrypted string.

        Args:
            ciphertext: Encrypted string to decrypt

        Returns:
            Decrypted plaintext string, or None if input is None
        """
        if ciphertext is None:
            return None
        return self._get_cipher().decrypt(ciphertext.encode()).decode()


# Singleton instance
encryption_service = EncryptionService()
