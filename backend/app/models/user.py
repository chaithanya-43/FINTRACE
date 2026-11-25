from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.types import TZDateTime
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200))
    phone_e164: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'citizen'")
    )
    account_status: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default=text("'active'")
    )
    is_email_verified: Mapped[bool] = mapped_column(
        nullable=False, server_default=text("false")
    )
    last_login_at: Mapped[datetime | None] = mapped_column(TZDateTime)

    __table_args__ = (
        CheckConstraint(
            "role IN ('citizen', 'investigator', 'administrator')",
            name="role",
        ),
        CheckConstraint(
            "account_status IN ('active', 'locked', 'suspended', 'deactivated')",
            name="account_status",
        ),
        CheckConstraint("char_length(email) >= 3", name="email_present"),
        Index("ix_users_email_lower", text("lower(email)"), unique=True),
        Index(
            "uq_users_phone_e164",
            "phone_e164",
            unique=True,
            postgresql_where=text("phone_e164 IS NOT NULL"),
        ),
        Index("ix_users_role", "role"),
        Index("ix_users_account_status", "account_status"),
    )
