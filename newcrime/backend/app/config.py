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

    # Catalyst Datastore
    use_catalyst: bool = False
    catalyst_project_id: str = ""
    catalyst_client_id: str = ""
    catalyst_client_secret: str = ""
    catalyst_refresh_token: str = ""
    catalyst_dc: str = "in"
    # Catalyst LLM serving (QuickML). The model id is the deployed serving
    # name, not a vendor name like "glm-4.7".
    glm_model_id: str = "crm-di-glm47b_30b_it"
    # CATALYST-ORG header required by the LLM endpoint (the environment id).
    catalyst_org_id: str = "60076341598"
    # QuickML published-endpoint key for the Prophet model. QuickML predicts
    # against an endpoint, not a model id.
    quickml_endpoint_key: str = ""
    # Catalyst LLM serving REST endpoint for the deployed chat model
    # (GLM 4.7 / Qwen 3.6), e.g.
    #   https://api.catalyst.zoho.in/quickml/v1/project/<id>/glm/chat
    # Requires a refresh token scoped for QuickML — the Datastore scopes are
    # not sufficient and the endpoint answers 401 INVALID_OAUTHSCOPE without it.
    glm_endpoint_url: str = ""

    # Catalyst File Store folder IDs
    evidence_folder_id: str = ""
    witness_folder_id: str = ""
    chat_uploads_folder_id: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
