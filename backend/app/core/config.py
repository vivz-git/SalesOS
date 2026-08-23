from functools import lru_cache

from pydantic import model_validator
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

    @model_validator(mode="before")
    @classmethod
    def populate_fallbacks(cls, values: dict) -> dict:
        import os
        if isinstance(values, dict):
            if not values.get("supabase_url"):
                for k in ["NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_PROJECT_URL"]:
                    if os.getenv(k):
                        values["supabase_url"] = os.getenv(k)
                        break
            if not values.get("supabase_publishable_key"):
                for k in ["SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"]:
                    if os.getenv(k):
                        values["supabase_publishable_key"] = os.getenv(k)
                        break
        return values


@lru_cache
def get_settings() -> Settings:
    return Settings()
