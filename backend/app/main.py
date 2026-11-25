import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import install_error_handlers
from app.core.logging import configure_logging

configure_logging(settings.debug)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "Financial Fraud Intelligence and Recovery Platform. Assessments are "
        "deterministic and source-referenced; FINTRACE does not file complaints "
        "or perform recovery actions on a user's behalf."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Evidence-SHA256", "Content-Disposition"],
)

install_error_handlers(app)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
def warn_about_default_secret() -> None:
    if settings.environment.lower() == "production" and "change-me" in settings.jwt_secret:
        logger.error(
            "JWT_SECRET is still the development default. Set a real secret before "
            "serving production traffic."
        )
