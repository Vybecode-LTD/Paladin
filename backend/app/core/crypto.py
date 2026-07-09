"""Symmetric encryption for secrets stored at rest (currently: SMTP
passwords). Separate from JWT signing (core/security.py) — this is for data
we need to read BACK in plaintext server-side, not for verifying a token."""
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings

_fernet = Fernet(settings.encryption_key.encode())


def encrypt_secret(plaintext: str) -> str:
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Could not decrypt stored secret — ENCRYPTION_KEY may have changed.")
