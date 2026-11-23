# API contracts

FastAPI generates OpenAPI documentation automatically.

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Initial endpoint

### Health check

`GET /api/v1/health`

Response:

```json
{
  "status": "ok"
}
```

## Contract conventions

- Keep versioned routes under `/api/v1`.
- Use Pydantic schemas for public request and response shapes.
- Return structured validation and error responses.
- Document sensitive fields and retention behavior explicitly.
- Future multilingual fields should use extensible schema design rather than hard-coded language variants.
