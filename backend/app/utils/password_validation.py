"""
bcrypt truncates/rejects input beyond 72 bytes. We never want to silently
truncate a user's password (that would quietly weaken it and could make two
different passwords hash identically), so we validate the UTF-8 byte length
up front and reject anything too long with a clear, actionable error.

This module has zero third-party dependencies so it can be:
  - imported by the Pydantic schema layer (schemas/auth.py)
  - imported by the hashing layer (utils/security.py) as defense-in-depth
  - unit tested on its own, without FastAPI/SQLAlchemy/passlib installed
"""
from __future__ import annotations

MAX_PASSWORD_BYTES = 72  # bcrypt's hard limit


class PasswordTooLongError(ValueError):
    """Raised when a password exceeds bcrypt's 72-byte limit."""


def password_byte_length(password: str) -> int:
    """UTF-8 byte length of the password — NOT Python's len(), which counts
    characters. A password full of multi-byte characters (emoji, accented
    letters, non-Latin scripts) can be short in characters but long in bytes."""
    return len(password.encode("utf-8"))


def validate_password_length(password: str) -> None:
    """Raises PasswordTooLongError if the password's UTF-8 byte length
    exceeds bcrypt's 72-byte limit. Does nothing (no truncation) otherwise."""
    byte_len = password_byte_length(password)
    if byte_len > MAX_PASSWORD_BYTES:
        raise PasswordTooLongError(
            f"Password must be 72 bytes or fewer (got {byte_len} bytes). "
            "If your password contains emoji or non-Latin characters, note "
            "that some characters take more than 1 byte."
        )
