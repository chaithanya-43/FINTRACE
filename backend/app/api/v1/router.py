from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    auth,
    cases,
    complaints,
    evidence,
    health,
    recovery,
    regulatory,
    transactions,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cases.router)
api_router.include_router(transactions.router)
api_router.include_router(evidence.router)
api_router.include_router(regulatory.router)
api_router.include_router(complaints.router)
api_router.include_router(recovery.router)
api_router.include_router(admin.router)
