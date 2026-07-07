import os


class Settings:
    project_id: str = os.getenv("CATALYST_PROJECT_ID", "")
    environment: str = os.getenv("CATALYST_ENVIRONMENT", "Development")
    app_env: str = os.getenv("APP_ENV", "development")
    api_base_url: str = os.getenv("API_BASE_URL", "")
    datastore_id: str = os.getenv("DATASTORE_IDENTIFIER", "ksp-dev-datastore")
    nosql_id: str = os.getenv("NOSQL_IDENTIFIER", "ksp-dev-conversation-nosql")
    stratus_bucket: str = os.getenv("STRATUS_BUCKET", "ksp-dev-report-stratus")
    cache_segment: str = os.getenv("CACHE_SEGMENT", "ksp-dev-query-cache")

    quickml_model_id: str = os.getenv("QUICKML_MODEL_ID", "quickml-llama-3.1-70b")
    kb_schema_id: str = os.getenv("KB_SCHEMA_ID", "ksp-dev-rag-kb-schema")
    kb_examples_id: str = os.getenv("KB_EXAMPLES_ID", "ksp-dev-rag-kb-examples")

    sql_timeout_seconds: int = int(os.getenv("SQL_TIMEOUT_SECONDS", "30"))
    sql_max_rows: int = int(os.getenv("SQL_MAX_ROWS", "1000"))
    sql_repair_max_retries: int = int(os.getenv("SQL_REPAIR_MAX_RETRIES", "2"))
    conversation_context_limit: int = int(os.getenv("CONVERSATION_CONTEXT_LIMIT", "10"))
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    rag_score_threshold: float = float(os.getenv("RAG_SCORE_THRESHOLD", "0.7"))

    model_temperature_nl2sql: float = float(os.getenv("MODEL_TEMPERATURE_NL2SQL", "0.1"))
    model_temperature_summary: float = float(os.getenv("MODEL_TEMPERATURE_SUMMARY", "0.3"))
    model_max_tokens: int = int(os.getenv("MODEL_MAX_TOKENS", "4096"))

    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    privacy_suppression_threshold: int = int(os.getenv("PRIVACY_SUPPRESSION_THRESHOLD", "5"))
    entity_match_fuzzy_threshold: int = int(os.getenv("ENTITY_MATCH_FUZZY_THRESHOLD", "85"))

    graph_max_depth: int = int(os.getenv("GRAPH_MAX_DEPTH", "3"))
    graph_max_nodes: int = int(os.getenv("GRAPH_MAX_NODES", "300"))
    graph_max_edges: int = int(os.getenv("GRAPH_MAX_EDGES", "800"))

    score_version: str = os.getenv("SCORE_VERSION", "1.0.0")
    forecast_model_version: str = os.getenv("FORECAST_MODEL_VERSION", "prophet_v1.0")
    forecast_horizon_days: int = int(os.getenv("FORECAST_HORIZON_DAYS", "30"))
    forecast_training_window_days: int = int(os.getenv("FORECAST_TRAINING_WINDOW_DAYS", "365"))
    alert_z_score_threshold: float = float(os.getenv("ALERT_Z_SCORE_THRESHOLD", "2.0"))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    trace_enabled: bool = os.getenv("TRACE_ENABLED", "true").lower() == "true"


settings = Settings()
