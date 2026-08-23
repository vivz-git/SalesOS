from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_service_role_key: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    resend_api_key: str | None = None
    resend_from_email: str = "onboarding@resend.dev"
    resend_webhook_secret: str | None = None
    hubspot_client_id: str | None = None
    hubspot_client_secret: str | None = None
    database_url: str = "postgresql+psycopg://localhost/postgres"
    worker_database_url: str = "postgresql+psycopg://localhost/postgres"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
