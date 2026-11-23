# FINTRACE

FINTRACE is a modular monolith for India's financial fraud intelligence and recovery ecosystem. It provides a foundation for registering incidents and cases, extracting and classifying fraud intelligence, applying source-backed regulatory assessments, maintaining evidence integrity, and planning recovery actions.

## Problem

Victims and investigators often work across fragmented complaint channels and evidence sources. FINTRACE aims to organize incident information, preserve evidence provenance, support consistent regulatory workflows, and provide traceable recovery progress without presenting AI-generated material as an authoritative legal or regulatory decision.

## Core capabilities

- Incident and case lifecycle management
- Incident extraction and fraud classification
- Deterministic, versioned regulatory rules and assessments
- Secure evidence storage and cryptographic integrity metadata
- Recovery action planning, complaint drafting support, and progress tracking
- Future multilingual interfaces and workflows

## Technology stack

- Frontend: React, Vite, JavaScript
- Backend: Python, FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- API documentation: OpenAPI / Swagger
- Configuration: Pydantic Settings and environment variables
- Testing: Pytest and Vitest

## Architecture

FINTRACE uses a modular monolith. API routes remain thin, business logic lives in backend modules, SQLAlchemy models remain separate from Pydantic schemas, and database sessions are provided through dependency injection. Modules are deployable together while retaining clear responsibility boundaries.

See [Architecture](docs/architecture.md), [Database design](docs/database-design.md), [API contracts](docs/api-contracts.md), [Development guide](docs/development-guide.md), and [Security guidelines](docs/security-guidelines.md).

## Project structure

```text
frontend/   React application
backend/    FastAPI application and modular domains
docs/       Architecture and operating documentation
storage/    Local storage area (not for committed evidence)
scripts/    Repository utility scripts
```

## Local setup

Prerequisites:

- Docker with Compose
- Python 3.11+
- Node.js 20+

Copy the environment examples and replace placeholders before running services:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### Database

```bash
docker compose up -d postgres
```

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://localhost:8000`, with Swagger at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173`.

## Architecture constraints

- No microservices in the initial system.
- Never store OTPs, UPI PINs, or banking passwords.
- AI may assist extraction and classification, but regulatory decisions use deterministic, versioned, source-backed rules.
- Evidence hashes verify byte integrity; a hash alone does not prove that evidence originated from the claimed source.
- No actual banking integrations are included.
