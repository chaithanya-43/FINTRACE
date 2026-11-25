import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RecoveryAction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "recovery_actions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    action_type: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)

    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'medium'")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'pending'")
    )
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'system'")
    )

    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )

    due_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    scheduled_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    completed_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    outcome_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'unknown'")
    )
    outcome_notes: Mapped[str | None] = mapped_column(Text)
    recovered_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    case = relationship("Case", back_populates="recovery_actions")

    __table_args__ = (
        CheckConstraint(
            "priority IN ('critical', 'high', 'medium', 'low')", name="priority"
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'skipped', 'blocked')",
            name="status",
        ),
        CheckConstraint("source IN ('system', 'user')", name="source"),
        CheckConstraint(
            "outcome_status IN ('unknown', 'pending', 'recovered', 'partially_recovered', 'not_recovered')",
            name="outcome_status",
        ),
        CheckConstraint(
            "completed_at IS NULL OR status = 'completed'", name="completed_consistency"
        ),
        CheckConstraint(
            "recovered_amount IS NULL OR recovered_amount >= 0",
            name="non_negative_recovered",
        ),
        Index("ix_recovery_actions_case_id", "case_id"),
        Index("ix_recovery_actions_case_status", "case_id", "status"),
        Index("ix_recovery_actions_priority", "priority"),
        Index("ix_recovery_actions_due_at", "due_at"),
    )
