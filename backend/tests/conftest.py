"""Test fixtures.

Tests run against a real PostgreSQL database because the guarantees under test
(CHECK constraints, composite foreign keys, append-only triggers, JSONB) do not
exist in SQLite. Set TEST_DATABASE_URL to point at a disposable database.
"""

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database import connection
from app.main import app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://fintrace:fintrace@127.0.0.1:55432/fintrace_test",
)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_TABLES = (
    "audit_events",
    "complaint_status_events",
    "regulatory_assessments",
    "evidence_signatures",
    "evidence",
    "transactions",
    "complaints",
    "recovery_actions",
    "regulatory_rules",
    "signing_keys",
    "cases",
    "users",
)


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL, future=True)

    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    alembic_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    alembic_config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_config, "head")

    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def clean_database(engine):
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE " + ", ".join(_TABLES) + " RESTART IDENTITY CASCADE")
        )
    yield


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session", autouse=True)
def evidence_storage():
    """Point evidence storage at a throwaway directory inside the project."""
    original = settings.storage_root
    storage_dir = Path(__file__).resolve().parent / ".evidence"
    storage_dir.mkdir(parents=True, exist_ok=True)
    settings.storage_root = str(storage_dir)
    yield
    settings.storage_root = original


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[connection.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def register(client: TestClient, email: str = "victim@example.com", password: str = "correct-horse-battery") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test Victim",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def account(client):
    payload = register(client)
    return {
        "token": payload["access_token"],
        "user": payload["user"],
        "headers": auth_headers(payload["access_token"]),
    }


@pytest.fixture()
def other_account(client):
    payload = register(client, email="other@example.com")
    return {
        "token": payload["access_token"],
        "user": payload["user"],
        "headers": auth_headers(payload["access_token"]),
    }


@pytest.fixture()
def case(client, account):
    response = client.post(
        "/api/v1/cases",
        headers=account["headers"],
        json={
            "title": "Unauthorised UPI debit",
            "description": (
                "I received a collect request pretending to be a refund and approved it. "
                "The money left my account immediately and the caller stopped responding."
            ),
            "incident_type": "upi_fraud",
            "fraud_channel": "upi",
            "incident_occurred_at": "2026-11-20T10:30:00Z",
            "estimated_loss_amount": "15000.00",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
