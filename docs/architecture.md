# Architecture

FINTRACE is a modular monolith. One FastAPI application and one frontend application provide the system boundaries; internal modules keep domain responsibilities separated.

## Backend layers

- `api/v1`: HTTP routing and thin endpoint handlers
- `modules`: business capabilities and domain workflows
- `schemas`: Pydantic request and response models
- `models`: SQLAlchemy persistence models
- `database`: engine, sessions, and declarative base
- `core`: configuration and security primitives
- `utils`: narrowly shared technical helpers

API endpoints should delegate business behavior to modules rather than embedding it in route functions. Models and schemas remain separate.

## Modules

- **cases**: incident and case lifecycle
- **incident_intelligence**: extraction and fraud classification
- **regulatory_engine**: deterministic, versioned regulatory rules
- **evidence**: secure storage and integrity metadata
- **recovery**: recovery planning and progress

## Dependency injection

Database access uses `get_db()` from `app.database.connection`. FastAPI routes can declare `Depends(get_db)` to receive a session that is closed after the request.

## Constraints

No microservices, banking integrations, or free-form LLM regulatory decisions are implemented in the initial system. Architecture should allow future localization and additional interfaces without changing core domain boundaries.
