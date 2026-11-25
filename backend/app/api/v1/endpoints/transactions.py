import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, load_authorized_case
from app.database.connection import get_db
from app.models import User
from app.modules.cases import transactions as service
from app.schemas.transaction import TransactionCreate, TransactionRead, TransactionUpdate

router = APIRouter(tags=["transactions"])


@router.get("/cases/{case_id}/transactions", response_model=list[TransactionRead])
def list_transactions(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TransactionRead]:
    load_authorized_case(case_id, user, db)
    return [TransactionRead.model_validate(item) for item in service.list_transactions(db, case_id)]


@router.post(
    "/cases/{case_id}/transactions",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    case_id: uuid.UUID,
    payload: TransactionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    case = load_authorized_case(case_id, user, db)
    transaction = service.create_transaction(
        db, case=case, user=user, data=payload.model_dump(exclude_unset=True)
    )
    return TransactionRead.model_validate(transaction)


@router.patch(
    "/cases/{case_id}/transactions/{transaction_id}", response_model=TransactionRead
)
def update_transaction(
    case_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    case = load_authorized_case(case_id, user, db)
    transaction = service.update_transaction(
        db,
        case=case,
        transaction_id=transaction_id,
        user=user,
        data=payload.model_dump(exclude_unset=True),
    )
    return TransactionRead.model_validate(transaction)
