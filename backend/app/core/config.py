from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FINTRACE"
    environment: str = "development"
    debug: bool = True
    database_url: str = (
        "postgresql+psycopg://fintrace:"
        "replace-with-a-local-placeholder@localhost:5432/fintrace"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
