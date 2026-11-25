import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(gt=0, le=Decimal("999999999999.99"))
    currency: str = Field(default="INR", min_length=3, max_length=3)
    transaction_at: datetime | None = None
    direction: str = Field(default="debit")
    authorization_type: str = Field(default="unknown")
    channel: str | None = Field(default=None, max_length=48)
    counterparty_name: str | None = Field(default=None, max_length=200)
    counterparty_account_masked: str | None = Field(default=None, max_length=64)
    utr_reference: str | None = Field(default=None, max_length=64)
    status: str = Field(default="reported")
    source: str = Field(default="user")
    verification_status: str = Field(default="user_confirmed")
    notes: str | None = Field(default=None, max_length=5000)


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal | None = Field(default=None, gt=0, le=Decimal("999999999999.99"))
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    transaction_at: datetime | None = None
    direction: str | None = None
    authorization_type: str | None = None
    channel: str | None = Field(default=None, max_length=48)
    counterparty_name: str | None = Field(default=None, max_length=200)
    counterparty_account_masked: str | None = Field(default=None, max_length=64)
    utr_reference: str | None = Field(default=None, max_length=64)
    status: str | None = None
    verification_status: str | None = None
    notes: str | None = Field(default=None, max_length=5000)


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    amount: Decimal
    currency: str
    transaction_at: datetime | None
    direction: str
    authorization_type: str
    channel: str | None
    counterparty_name: str | None
    counterparty_account_masked: str | None
    utr_reference: str | None
    status: str
    source: str
    verification_status: str
    notes: str | None
    created_at: datetime
