from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    database_url: str = "sqlite:///./support.db"
    observability_db_path: str = "database/observability.db"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    auth_secret: str = "local-development-secret-change-before-deploy"
    max_message_length: int = 4000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def require_production_secret(self):
        if self.app_env == "production" and (len(self.auth_secret) < 32 or self.auth_secret == "local-development-only"):
            raise ValueError("AUTH_SECRET must be a unique value with at least 32 characters in production.")
        return self


settings = Settings()