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
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Transaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "transactions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    transaction_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default=text("'INR'")
    )
    direction: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'debit'")
    )
    authorization_type: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'unknown'")
    )
    channel: Mapped[str | None] = mapped_column(String(48))
    counterparty_name: Mapped[str | None] = mapped_column(String(200))
    counterparty_account_masked: Mapped[str | None] = mapped_column(String(64))
    utr_reference: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'reported'")
    )
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default=text("'user'")
    )
    verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'user_confirmed'")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    recorded_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id")
    )

    case = relationship("Case", back_populates="transactions")
    evidence_items = relationship(
        "Evidence",
        back_populates="transaction",
        viewonly=True,
        overlaps="case,evidence_items",
    )

    __table_args__ = (
        # Consumed by the composite foreign key on evidence so an evidence row
        # can never point at a transaction belonging to a different case.
        UniqueConstraint("id", "case_id", name="uq_transactions_id_case_id"),
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("char_length(currency) = 3", name="currency_iso3"),
        CheckConstraint("direction IN ('debit', 'credit')", name="direction"),
        CheckConstraint(
            "authorization_type IN ('unauthorized', 'authorized_deceived', 'unknown')",
            name="authorization_type",
        ),
        CheckConstraint(
            "status IN ('reported', 'disputed', 'reversed', 'chargeback', 'unresolved')",
            name="status",
        ),
        CheckConstraint("source IN ('user', 'evidence', 'extracted')", name="source"),
        CheckConstraint(
            "verification_status IN ('unverified', 'user_confirmed', 'disputed')",
            name="verification_status",
        ),
        Index("ix_transactions_case_id", "case_id"),
        Index("ix_transactions_occurred_at", "transaction_at"),
        Index("ix_transactions_verification_status", "verification_status"),
        Index("ix_transactions_source", "source"),
        # A UTR may legitimately be absent; it may not be repeated inside a case.
        Index(
            "uq_transactions_case_utr",
            "case_id",
            "utr_reference",
            unique=True,
            postgresql_where=text("utr_reference IS NOT NULL"),
        ),
    )
