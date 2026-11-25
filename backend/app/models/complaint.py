import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Complaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A complaint the user filed themselves. FINTRACE never submits it."""

    __tablename__ = "complaints"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(48), nullable=False)
    organisation_name: Mapped[str | None] = mapped_column(String(200))
    reference_number: Mapped[str | None] = mapped_column(String(120))
    prepared_payload: Mapped[dict | None] = mapped_column(JSONB)

    submission_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'draft'")
    )
    # Nullable by design: the official status is unknown until observed.
    official_status: Mapped[str | None] = mapped_column(String(48))
    official_status_detail: Mapped[str | None] = mapped_column(Text)
    official_status_source_url: Mapped[str | None] = mapped_column(Text)
    is_disputed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    filed_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    acknowledged_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    closed_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    last_checked_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    case = relationship("Case", back_populates="complaints")
    status_events = relationship(
        "ComplaintStatusEvent",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintStatusEvent.checked_at",
    )

    __table_args__ = (
        CheckConstraint(
            "submission_status IN ('draft', 'ready', 'submitted', 'acknowledged', 'rejected', 'withdrawn')",
            name="submission_status",
        ),
        CheckConstraint(
            "submission_status NOT IN ('submitted', 'acknowledged') OR filed_at IS NOT NULL",
            name="filed_at_present",
        ),
        CheckConstraint(
            "submission_status <> 'acknowledged' OR acknowledged_at IS NOT NULL",
            name="acknowledged_at_present",
        ),
        CheckConstraint(
            "closed_at IS NULL OR filed_at IS NOT NULL", name="closed_requires_filed"
        ),
        Index("ix_complaints_case_id", "case_id"),
        Index("ix_complaints_case_channel", "case_id", "channel"),
        Index("ix_complaints_submission_status", "submission_status"),
        Index("ix_complaints_official_status", "official_status"),
    )
