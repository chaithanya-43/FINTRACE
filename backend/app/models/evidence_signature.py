import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class EvidenceSignature(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Append-only: a signature row is never rewritten after insert."""

    __tablename__ = "evidence_signatures"

    evidence_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        nullable=False,
    )
    signing_key_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("signing_keys.id")
    )
    key_id_snapshot: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'Ed25519'")
    )
    signature_b64: Mapped[str] = mapped_column(Text, nullable=False)
    signed_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    verification_result: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'unverified'")
    )

    evidence = relationship("Evidence", back_populates="signatures")

    __table_args__ = (
        UniqueConstraint(
            "evidence_id", "signature_b64", name="uq_evidence_signatures_signature"
        ),
        CheckConstraint(
            "verification_result IN ('unverified', 'valid', 'invalid')",
            name="verification_result",
        ),
        Index("ix_evidence_signatures_evidence_id", "evidence_id"),
    )
