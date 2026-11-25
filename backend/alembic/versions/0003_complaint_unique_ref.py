"""add unique partial index for complaint channel reference per case

Revision ID: 0003_complaint_unique_ref
Revises: 0002_immutability_guards
Create Date: 2026-11-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_complaint_unique_ref"
down_revision: Union[str, None] = "0002_immutability_guards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "uq_complaints_case_channel_reference",
        "complaints",
        ["case_id", "channel", "reference_number"],
        unique=True,
        postgresql_where=sa.text("reference_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_complaints_case_channel_reference", table_name="complaints")
