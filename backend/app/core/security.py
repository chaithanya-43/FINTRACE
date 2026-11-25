"""Password hashing and access-token primitives.

Passwords are hashed with Argon2id. Tokens are signed JWTs (HS256 by default)
containing only the subject identifier, the role snapshot and standard claims.
"""

from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import settings

_password_hasher = PasswordHasher()


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired or mis-signed."""


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_hash_needs_rehash(password_hash: str) -> bool:
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return True


def create_access_token(
    subject: str,
    role: str,
    expires_minutes: int | None = None,
) -> tuple[str, int]:
    """Return ``(token, expires_in_seconds)``."""
    minutes = expires_minutes or settings.access_token_minutes
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=minutes)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "typ": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, minutes * 60


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as exc:  # covers expiry, signature and format errors
        raise TokenError("Access token is invalid or has expired.") from exc
    if payload.get("typ") != "access" or not payload.get("sub"):
        raise TokenError("Access token is invalid or has expired.")
    return payload
