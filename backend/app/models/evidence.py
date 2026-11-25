import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Evidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "evidence"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True))
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    evidence_type: Mapped[str] = mapped_column(
        String(48), nullable=False, server_default=text("'other'")
    )
    description: Mapped[str | None] = mapped_column(Text)
    collected_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    verification_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'unverified'")
    )
    verified_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    chain_of_custody: Mapped[list | dict | None] = mapped_column(JSONB)

    case = relationship("Case", back_populates="evidence_items")
    transaction = relationship(
        "Transaction",
        back_populates="evidence_items",
        foreign_keys=[transaction_id, case_id],
        viewonly=True,
    )
    signatures = relationship(
        "EvidenceSignature", back_populates="evidence", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Same-case guarantee: the target transaction must belong to this case.
        ForeignKeyConstraint(
            ["transaction_id", "case_id"],
            ["transactions.id", "transactions.case_id"],
            name="fk_evidence_transaction_case",
        ),
        UniqueConstraint("id", "case_id", name="uq_evidence_id_case_id"),
        CheckConstraint("byte_size > 0", name="byte_size_positive"),
        CheckConstraint("sha256_hash ~ '^[0-9a-f]{64}$'", name="sha256_format"),
        CheckConstraint(
            "verification_status IN ('unverified', 'verified', 'failed')",
            name="verification_status",
        ),
        CheckConstraint(
            "verified_at IS NULL OR verification_status <> 'unverified'",
            name="verified_at_consistency",
        ),
        # Deliberately NOT unique: the same bytes may be submitted twice.
        Index("ix_evidence_case_id", "case_id"),
        Index("ix_evidence_sha256_hash", "sha256_hash"),
        Index("ix_evidence_transaction_id", "transaction_id"),
    )
