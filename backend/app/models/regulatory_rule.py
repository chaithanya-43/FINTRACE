from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RegulatoryRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Versioned, source-backed rule. Immutable once active (enforced in SQL)."""

    __tablename__ = "regulatory_rules"

    rule_code: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'IN'")
    )
    authority: Mapped[str] = mapped_column(String(200), nullable=False)
    source_reference: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date)
    rule_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    engine_schema_version: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'1.0'")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'draft'")
    )
    verification_status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'unverified'")
    )
    verified_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    verified_by: Mapped[str | None] = mapped_column(String(200))
    notes: Mapped[str | None] = mapped_column(Text)
    superseded_by_rule_id: Mapped[None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("regulatory_rules.id")
    )

    __table_args__ = (
        UniqueConstraint("rule_code", "version", name="uq_regulatory_rules_code_version"),
        CheckConstraint(
            "status IN ('draft', 'active', 'deprecated', 'superseded')", name="status"
        ),
        CheckConstraint(
            "verification_status IN ('unverified', 'verified')",
            name="verification_status",
        ),
        CheckConstraint("version > 0", name="version_positive"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="effective_window",
        ),
        Index("ix_regulatory_rules_authority_rule_code", "authority", "rule_code"),
        Index("ix_regulatory_rules_status_effective_from", "status", "effective_from"),
    )
