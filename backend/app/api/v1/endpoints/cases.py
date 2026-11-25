import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, load_authorized_case, visible_case_query
from app.database.connection import get_db
from app.models import Case, User
from app.modules.audit import service as audit_service
from app.modules.cases import dashboard, service
from app.modules.incident_intelligence import service as intelligence
from app.schemas.audit import AnalysisResponse, AuditEventRead, DashboardSummary
from app.schemas.case import CaseCreate, CaseRead, CaseSummary, CaseUpdate
from app.schemas.common import Message
from app.utils.enums import CaseStatus, Role

router = APIRouter(tags=["cases"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> DashboardSummary:
    return DashboardSummary(**dashboard.summary(db, user=user))


@router.post("/cases", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseRead:
    case = service.create_case(db, user=user, data=payload.model_dump(exclude_unset=True))
    return CaseRead.model_validate(case)


@router.get("/cases", response_model=list[CaseRead])
def list_cases(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    include_archived: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CaseRead]:
    statement = visible_case_query(user)
    if not include_archived:
        statement = statement.where(Case.is_archived.is_(False))
    statement = statement.order_by(Case.created_at.desc()).limit(limit).offset(offset)
    return [CaseRead.model_validate(case) for case in db.scalars(statement)]


@router.get("/cases/{case_id}", response_model=CaseRead)
def read_case(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseRead:
    case = load_authorized_case(case_id, user, db)
    return CaseRead.model_validate(case)


@router.get("/cases/{case_id}/summary", response_model=CaseSummary)
def read_case_summary(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseSummary:
    load_authorized_case(case_id, user, db)
    return CaseSummary(**service.case_summary(db, case_id))


@router.patch("/cases/{case_id}", response_model=CaseRead)
def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseRead:
    case = load_authorized_case(case_id, user, db)
    case = service.update_case(db, case=case, user=user, data=payload.model_dump(exclude_unset=True))
    return CaseRead.model_validate(case)


@router.post("/cases/{case_id}/status", response_model=CaseRead)
def change_case_status(
    case_id: uuid.UUID,
    payload: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaseRead:
    case = load_authorized_case(case_id, user, db)
    target = str(payload.get("internal_status", ""))
    case = service.change_status(db, case=case, user=user, target_status=target)
    return CaseRead.model_validate(case)


@router.post("/cases/{case_id}/archive", response_model=Message)
def archive_case(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Message:
    case = load_authorized_case(case_id, user, db)
    if user.role == Role.CITIZEN and case.created_by_user_id != user.id:
        from app.core.exceptions import Forbidden

        raise Forbidden("Only the case owner can archive this case.")
    service.archive_case(db, case=case, user=user)
    return Message(message="Case archived.")


@router.post("/cases/{case_id}/analyze", response_model=AnalysisResponse)
def analyse_case(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResponse:
    case = load_authorized_case(case_id, user, db)
    return AnalysisResponse(**intelligence.analyse(db, case=case, user=user))


@router.get("/cases/{case_id}/audit", response_model=list[AuditEventRead])
def read_audit(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=200, ge=1, le=500),
) -> list[AuditEventRead]:
    load_authorized_case(case_id, user, db)
    return [AuditEventRead.model_validate(event) for event in audit_service.list_for_case(db, case_id, limit)]


@router.get("/cases/{case_id}/progress")
def case_progress(
    case_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    case = load_authorized_case(case_id, user, db)
    counts = service.case_summary(db, case_id)
    return {
        "case_id": str(case.id),
        "internal_status": case.internal_status,
        "completeness_status": case.completeness_status,
        "is_archived": case.is_archived,
        "steps": [status_value.value for status_value in CaseStatus],
        "summary": {key: value for key, value in counts.items() if key != "case_id"},
    }
