"""Optional Ed25519 signing.

Signing requires a key configured through the environment. When no key is
present the application reports signing as unavailable; it never fabricates a
signature or marks unsigned evidence as signed.
"""

import base64
import binascii
from datetime import UTC, datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import SigningKey


class SigningUnavailable(Exception):
    pass


class SigningError(Exception):
    pass


def _decode_private_key(value: str) -> Ed25519PrivateKey:
    text = value.strip()
    if text.startswith("-----BEGIN"):
        key = serialization.load_pem_private_key(text.encode(), password=None)
        if not isinstance(key, Ed25519PrivateKey):
            raise SigningError("Configured PEM key is not an Ed25519 private key.")
        return key
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise SigningError("ED25519_PRIVATE_KEY_B64 is not valid base64.") from exc
    if len(raw) == 32:
        return Ed25519PrivateKey.from_private_bytes(raw)
    try:
        key = serialization.load_der_private_key(raw, password=None)
    except Exception as exc:  # noqa: BLE001
        raise SigningError(
            "Configured key must be a 32-byte base64 seed, DER or PEM Ed25519 key."
        ) from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise SigningError("Configured key is not an Ed25519 private key.")
    return key


def is_configured() -> bool:
    return bool(settings.ed25519_private_key_b64) or bool(settings.ed25519_public_key_b64)


def key_id() -> str:
    return settings.ed25519_key_id or "unconfigured"


def public_key_b64() -> str:
    if settings.ed25519_public_key_b64 and not settings.ed25519_private_key_b64:
        return settings.ed25519_public_key_b64.strip()
    private_key = _decode_private_key(settings.ed25519_private_key_b64 or "")
    raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode()


def signing_payload(sha256_hash: str) -> bytes:
    return f"sha256:{sha256_hash}".encode()


def sign_hash(sha256_hash: str) -> str:
    if not settings.ed25519_private_key_b64:
        raise SigningUnavailable(
            "Evidence signing is not configured. Set ED25519_KEY_ID and "
            "ED25519_PRIVATE_KEY_B64 to enable signing."
        )
    signature = _decode_private_key(settings.ed25519_private_key_b64).sign(
        signing_payload(sha256_hash)
    )
    return base64.b64encode(signature).decode()


def verify_signature(signature_b64: str, sha256_hash: str, public_key_value: str) -> bool:
    try:
        raw = base64.b64decode(public_key_value, validate=True)
    except (binascii.Error, ValueError):
        return False
    try:
        key = Ed25519PublicKey.from_public_bytes(raw)
        key.verify(base64.b64decode(signature_b64), signing_payload(sha256_hash))
        return True
    except (InvalidSignature, ValueError, binascii.Error):
        return False


def ensure_registered_key(db: Session) -> SigningKey | None:
    """Return the configured key's registry row, creating it once if needed."""
    if not is_configured():
        return None
    identifier = key_id()
    existing = db.scalar(select(SigningKey).where(SigningKey.key_id == identifier))
    if existing is not None:
        return existing
    record = SigningKey(
        key_id=identifier,
        algorithm="Ed25519",
        public_key_b64=public_key_b64(),
        owner_type="platform",
        environment=settings.environment,
        valid_from=datetime.now(UTC),
        status="active",
    )
    db.add(record)
    db.flush()
    return record
