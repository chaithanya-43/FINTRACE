import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Case(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cases"

    public_reference: Mapped[str] = mapped_column(String(24), nullable=False)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    incident_type: Mapped[str] = mapped_column(
        String(48), nullable=False, server_default=text("'unknown'")
    )
    fraud_channel: Mapped[str] = mapped_column(
        String(48), nullable=False, server_default=text("'unknown'")
    )
    incident_occurred_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    incident_date: Mapped[date | None] = mapped_column(Date)

    estimated_loss_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default=text("'INR'")
    )

    internal_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'intake'")
    )
    completeness_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'incomplete'")
    )
    data_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    is_disputed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    archived_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    reporting_details: Mapped[str | None] = mapped_column(Text)

    creator = relationship("User", foreign_keys=[created_by_user_id], lazy="joined")
    assignee = relationship("User", foreign_keys=[assigned_to_user_id], lazy="joined")
    transactions = relationship(
        "Transaction",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="Transaction.transaction_at.desc()",
    )
    evidence_items = relationship("Evidence", back_populates="case")
    assessments = relationship(
        "RegulatoryAssessment",
        back_populates="case",
        order_by="RegulatoryAssessment.assessed_at.desc()",
    )
    complaints = relationship("Complaint", back_populates="case")
    document_drafts = relationship(
        "DocumentDraft",
        back_populates="case",
        cascade="all, delete-orphan",
        order_by="DocumentDraft.updated_at.desc()",
    )
    recovery_actions = relationship(
        "RecoveryAction",
        back_populates="case",
        order_by="RecoveryAction.created_at",
    )

    __table_args__ = (
        UniqueConstraint("public_reference", name="uq_cases_public_reference"),
        CheckConstraint(
            "internal_status IN ('intake', 'collecting_evidence', 'assessment', 'recovery', 'closed')",
            name="internal_status",
        ),
        CheckConstraint(
            "completeness_status IN ('incomplete', 'partial', 'complete')",
            name="completeness_status",
        ),
        CheckConstraint(
            "estimated_loss_amount IS NULL OR estimated_loss_amount >= 0",
            name="non_negative_loss",
        ),
        CheckConstraint("char_length(currency) = 3", name="currency_iso3"),
        CheckConstraint(
            "data_confidence IS NULL OR (data_confidence >= 0 AND data_confidence <= 1)",
            name="data_confidence_range",
        ),
        CheckConstraint(
            "is_archived = false OR archived_at IS NOT NULL",
            name="archived_requires_timestamp",
        ),
        Index("ix_cases_created_by_user_id", "created_by_user_id"),
        Index("ix_cases_assigned_to_user_id", "assigned_to_user_id"),
        Index("ix_cases_internal_status", "internal_status"),
        Index("ix_cases_incident_type", "incident_type"),
        Index("ix_cases_created_at", text("created_at DESC")),
        Index("ix_cases_active", "created_at", postgresql_where=text("NOT is_archived")),
    )
