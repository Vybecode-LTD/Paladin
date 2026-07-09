"""Symmetric encryption for secrets stored at rest (currently: SMTP
passwords). Separate from JWT signing (core/security.py) — this is for data
we need to read BACK in plaintext server-side, not for verifying a token.

The Fernet instance is built lazily (on first actual use), not at import
time: this module is imported by app.main's router chain, so an eager,
module-level Fernet(...) call means an unconfigured/invalid ENCRYPTION_KEY
crashes the ENTIRE app at startup — including totally unrelated features
(the public site, auth, blog) — over a secret that only matters once SMTP
settings are actually saved or used. Deferring construction scopes a
missing/bad key to just the SMTP feature, with a clear error at the point
of use, instead of taking the whole service down."""
from functools import lru_cache
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    try:
        return Fernet(settings.encryption_key.encode())
    except (ValueError, TypeError):
        raise ValueError(
            "ENCRYPTION_KEY is missing or invalid — set a real Fernet key "
            "(see backend/.env.example) before using SMTP settings."
        )


def encrypt_secret(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        raise ValueError("Could not decrypt stored secret — ENCRYPTION_KEY may have changed.")
