from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FINTRACE"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+psycopg" + "://" + "fintrace" + ":"
        + "replace-with-a-local-placeholder"
        + "@localhost:5432/fintrace"
    )

    # Authentication. Replace through environment configuration before any
    # non-local deployment; the default is deliberately recognisable.
    jwt_secret: str = "change-me-development-only-not-a-production-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 120

    # Comma separated list of browser origins allowed to call the API.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Evidence storage. Files never live inside a publicly served directory.
    storage_root: str = "storage"
    max_upload_bytes: int = 10 * 1024 * 1024
    allowed_evidence_types: str = (
        "application/pdf,image/png,image/jpeg,image/webp,text/plain,"
        "application/zip,application/octet-stream"
    )

    # Ed25519 signing is optional. When no key is configured the signing
    # endpoints report "unavailable" instead of pretending to sign.
    ed25519_key_id: str | None = None
    ed25519_private_key_b64: str | None = None
    ed25519_public_key_b64: str | None = None

    regulatory_engine_version: str = "1.0.0"
    regulatory_schema_version: str = "1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_evidence_type_list(self) -> list[str]:
        return [
            value.strip().lower()
            for value in self.allowed_evidence_types.split(",")
            if value.strip()
        ]


settings = Settings()
