"""add document_drafts table for Document & Complaint Assistant

Revision ID: 0004_document_drafts
Revises: 0003_complaint_unique_ref
Create Date: 2026-11-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004_document_drafts"
down_revision: Union[str, None] = "0003_complaint_unique_ref"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_drafts",
        sa.Column("case_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(length=48), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("recipient", sa.String(length=240), nullable=False),
        sa.Column("subject", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intake_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attachments_checklist", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("draft_status", sa.String(length=24), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("draft_status IN ('draft', 'reviewed', 'exported')", name="ck_document_drafts_draft_status"),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE", name="fk_document_drafts_case_id_cases"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name="fk_document_drafts_created_by_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_document_drafts"),
    )
    op.create_index("ix_document_drafts_case_id", "document_drafts", ["case_id"], unique=False)
    op.create_index("ix_document_drafts_case_type", "document_drafts", ["case_id", "document_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_document_drafts_case_type", table_name="document_drafts")
    op.drop_index("ix_document_drafts_case_id", table_name="document_drafts")
    op.drop_table("document_drafts")
