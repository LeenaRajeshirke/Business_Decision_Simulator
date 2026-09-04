"""
Password hashing.

IMPLEMENTATION NOTE — read before touching this file:

We hash directly with the `bcrypt` package's own API (`bcrypt.hashpw` /
`bcrypt.checkpw`), NOT via passlib's `CryptContext`.

ROOT CAUSE of "password cannot be longer than 72 bytes, truncate manually
if necessary" firing even for ordinary, short passwords: passlib 1.7.4
(its last release, 2020, now unmaintained) runs a one-time bcrypt-backend
self-test the first time it hashes anything. That self-test deliberately
hashes an over-long (>72 byte) probe string to detect which bcrypt variant
is installed. Modern bcrypt (>=4.0) removed the `__about__` submodule
passlib's detection code reads, and (>=4.1) changed its handling of
over-length input to raise ValueError instead of the old silent behavior.
Passlib's probe does not catch that ValueError, so it escapes on the
*first* hash call of the process — regardless of the real password's
length. Pinning bcrypt to an older release does not reliably fix this,
since the `__about__` removal alone (present since bcrypt 4.0.0) is
already enough to break passlib's detection path.

Calling the `bcrypt` library directly sidesteps passlib's stale
compatibility shim entirely — bcrypt itself is actively maintained.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from ..config import settings
from .password_validation import validate_password_length

logger = logging.getLogger(__name__)

# --- TEMPORARY DIAGNOSTIC ---------------------------------------------------
# Set AUTH_DEBUG=true in the environment to log non-sensitive details about
# each hash/verify call: byte length of the input, bcrypt version in use,
# and which function ran. The actual password is NEVER logged, in any form,
# at any level — only its byte length. Safe to leave off (default false) in
# normal operation. This is meant to be removed once you've confirmed this
# fix is active in your deployment; it is not required for the fix to work.
_AUTH_DEBUG = os.getenv("AUTH_DEBUG", "false").lower() == "true"


def _log_diagnostic(step: str, password: str) -> None:
    if not _AUTH_DEBUG:
        return
    logger.info(
        "[auth-diagnostic] step=%s byte_length=%d char_length=%d "
        "bcrypt_version=%s hashing_library=bcrypt (passlib not used)",
        step,
        len(password.encode("utf-8")),
        len(password),
        getattr(bcrypt, "__version__", "unknown"),
    )
# -----------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """Raises PasswordTooLongError if password exceeds bcrypt's 72-byte
    limit. Never truncates — the schema layer (schemas/auth.py) is expected
    to reject over-length passwords before this is called; this check is
    defense-in-depth for any code path that calls hash_password directly."""
    validate_password_length(password)
    _log_diagnostic("hash_password", password)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Raises PasswordTooLongError if the supplied password exceeds bcrypt's
    72-byte limit. Returns False (never raises) if `hashed` isn't a
    well-formed bcrypt hash — that's an authentication failure, not a
    validation error, and we don't want to leak details about why a
    comparison failed."""
    validate_password_length(plain)
    _log_diagnostic("verify_password", plain)
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        logger.warning("verify_password: stored value is not a valid bcrypt hash.")
        return False


def create_access_token(user_id: int, expires_minutes: int | None = None) -> str:
    settings.validate()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Returns the user_id encoded in the token, or raises jwt exceptions on failure."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return int(payload["sub"])
