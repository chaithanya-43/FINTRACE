import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
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
from app.models.mixins import UUIDPrimaryKeyMixin


class RegulatoryAssessment(Base, UUIDPrimaryKeyMixin):
    """Write-once assessment result with a full rule and input snapshot.

    Only the human-review columns may change after insert; the SQL guard
    trigger in migration 0002 enforces this for every caller.
    """

    __tablename__ = "regulatory_assessments"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("regulatory_rules.id"), nullable=False
    )

    # Rule snapshot, so a later rule revision cannot rewrite history.
    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_version: Mapped[int] = mapped_column(nullable=False)
    rule_title: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_authority: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    rule_source_url: Mapped[str | None] = mapped_column(Text)
    rule_verification_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'unverified'")
    )

    result_status: Mapped[str] = mapped_column(String(24), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    matched_conditions: Mapped[list | None] = mapped_column(JSONB)
    unmatched_conditions: Mapped[list | None] = mapped_column(JSONB)
    missing_facts: Mapped[list | None] = mapped_column(JSONB)

    input_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    input_snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    incident_occurred_at_snapshot: Mapped[datetime | None] = mapped_column(TZDateTime)
    applicable_on_date: Mapped[date] = mapped_column(Date, nullable=False)

    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False)
    assessed_at: Mapped[datetime] = mapped_column(
        TZDateTime, nullable=False, server_default=text("now()")
    )
    assessed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )

    review_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'unreviewed'")
    )
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    review_note: Mapped[str | None] = mapped_column(Text)

    supersedes_assessment_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("regulatory_assessments.id")
    )

    case = relationship("Case", back_populates="assessments")
    rule = relationship("RegulatoryRule")

    __table_args__ = (
        CheckConstraint(
            "result_status IN ('applies', 'may_apply', 'does_not_apply', 'inconclusive', 'disputed')",
            name="result_status",
        ),
        CheckConstraint(
            "review_status IN ('unreviewed', 'confirmed', 'rejected', 'disputed')",
            name="review_status",
        ),
        CheckConstraint(
            "rule_verification_status IN ('unverified', 'verified')",
            name="rule_verification_status",
        ),
        CheckConstraint(
            "reviewed_at IS NULL OR reviewed_by_user_id IS NOT NULL",
            name="reviewed_requires_reviewer",
        ),
        Index("ix_regulatory_assessments_case_assessed_at", "case_id", text("assessed_at DESC")),
        Index("ix_regulatory_assessments_rule_id", "rule_id"),
        Index("ix_regulatory_assessments_result_status", "result_status"),
        Index("ix_regulatory_assessments_supersedes", "supersedes_assessment_id"),
    )
