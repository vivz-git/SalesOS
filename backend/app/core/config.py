from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    log_level: str = "INFO"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_service_role_key: str | None = None
    gemini_api_key: str | None = None
    google_api_key: str | None = None
    resend_api_key: str | None = None
    resend_from_email: str = "onboarding@resend.dev"
    resend_webhook_secret: str | None = None
    hubspot_client_id: str | None = None
    hubspot_client_secret: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
