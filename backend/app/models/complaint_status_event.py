import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ComplaintStatusEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Append-only observation of an externally reported complaint status."""

    __tablename__ = "complaint_status_events"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_status: Mapped[str] = mapped_column(String(48), nullable=False)
    status_detail: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    checked_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    complaint = relationship("Complaint", back_populates="status_events")

    __table_args__ = (
        # Repeating an identical observation is a no-op, not a duplicate row.
        UniqueConstraint(
            "complaint_id",
            "checked_at",
            "observed_status",
            name="uq_complaint_status_events_observation",
        ),
        Index("ix_complaint_status_events_complaint_id", "complaint_id"),
        Index("ix_complaint_status_events_checked_at", text("checked_at DESC")),
    )
