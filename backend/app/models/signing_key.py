"""Signing key registry. Private key material is never stored in the database."""

from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SigningKey(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "signing_keys"

    key_id: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'Ed25519'")
    )
    public_key_b64: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_type: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'platform'")
    )
    owner_reference: Mapped[str | None] = mapped_column(String(200))
    environment: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'development'")
    )
    valid_from: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(TZDateTime)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'active'")
    )

    __table_args__ = (
        UniqueConstraint("key_id", name="uq_signing_keys_key_id"),
        CheckConstraint("status IN ('active', 'retired', 'revoked')", name="status"),
        CheckConstraint(
            "owner_type IN ('platform', 'organisation', 'user')", name="owner_type"
        ),
        CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="validity_window"),
        Index("ix_signing_keys_status", "status"),
    )
