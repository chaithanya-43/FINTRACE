import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DocumentDraft(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Editable draft complaint or dispute letter prepared for a case.

    FINTRACE prepares draft documents for the user to review and submit
    themselves; a saved draft does not represent an official submission.
    """

    __tablename__ = "document_drafts"

    case_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    recipient: Mapped[str] = mapped_column(String(240), nullable=False)
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intake_answers: Mapped[dict | None] = mapped_column(JSONB)
    attachments_checklist: Mapped[list | None] = mapped_column(JSONB)
    draft_status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default=text("'draft'")
    )

    case = relationship("Case", back_populates="document_drafts")

    __table_args__ = (
        CheckConstraint(
            "draft_status IN ('draft', 'reviewed', 'exported')",
            name="draft_status",
        ),
        Index("ix_document_drafts_case_id", "case_id"),
        Index("ix_document_drafts_case_type", "case_id", "document_type"),
    )
