"""Application configuration. Reads from environment / .env."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider slot -- defaults to the offline mock engine.
    llm_provider: str = "mock"          # mock | catalyst | openai
    catalyst_api_key: str = ""
    catalyst_endpoint: str = ""
    catalyst_model: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    database_url: str = "sqlite:///./crimeintel.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    secret_key: str = "dev-secret-change-me"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
