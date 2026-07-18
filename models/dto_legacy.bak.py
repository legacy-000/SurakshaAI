from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class LoginRequestDTO(BaseModel):
    kgid: str
    password: str


class UserContextDTO(BaseModel):
    user_id: str
    kgid: str
    first_name: str
    email: str
    role_id: int
    role_name: str
    unit_id: Optional[int] = None
    district_id: Optional[int] = None
    language_preference: str = "en"


class AuthorizationScopeDTO(BaseModel):
    user_id: str
    role_id: int
    permitted_apis: list[str] = []
    permitted_screens: list[str] = []
    permitted_tables: list[str] = []
    can_view_sql: bool = False
    can_export_pdf: bool = True
    can_view_pii: bool = False
    row_scope_type: Optional[str] = None
    row_scope_value: Optional[int] = None


class RawQueryDTO(BaseModel):
    message: str
    lang: str = "en"
    conversation_id: Optional[str] = None
    requested_format: str = "auto"


class QueryRequestDTO(RawQueryDTO):
    pass


class DetectedLanguageDTO(BaseModel):
    language_code: str = "en"
    confidence: float = 1.0


class NormalizedQueryDTO(BaseModel):
    original_text: str
    normalized_text: str
    language_code: str = "en"


class ExtractedEntityDTO(BaseModel):
    entity_type: str
    entity_value: str
    confidence: float = 1.0


class IntentResultDTO(BaseModel):
    intent_type: str = "DATA_QUERY"
    confidence: float = 1.0


class RetrievedSchemaContextDTO(BaseModel):
    table_descriptions: list[dict[str, Any]] = []
    column_descriptions: list[dict[str, Any]] = []


class QueryPlanDTO(BaseModel):
    tables: list[str] = []
    joins: list[dict[str, str]] = []
    filters: list[dict[str, Any]] = []
    aggregations: list[dict[str, str]] = []
    order_by: Optional[str] = None
    limit: Optional[int] = None


class GeneratedSQLDTO(BaseModel):
    query_plan: QueryPlanDTO
    sql_text: str
    model_version: str = "quickml-llama-3.1-70b-v1"
    prompt_version: str = "nl2sql-v2.1"


class SQLValidationResultDTO(BaseModel):
    is_valid: bool = True
    validated_sql: str = ""
    errors: list[str] = []
    warnings: list[str] = []


class SecuredSQLDTO(BaseModel):
    sql_text: str
    max_rows: int = 1000
    timeout_seconds: int = 30


class QueryExecutionResultDTO(BaseModel):
    query_id: str
    sql_text: str
    execution_status: str = "success"
    row_count: int = 0
    columns: list[str] = []
    rows: list[list[Any]] = []
    execution_time_ms: int = 0
    error_code: Optional[str] = None


class EvidenceReferenceDTO(BaseModel):
    evidence_id: str
    evidence_type: str = "database_fact"
    source_table: Optional[str] = None
    source_record_count: Optional[int] = None
    filter_summary: Optional[str] = None
    display_label: Optional[str] = None
    confidence: float = 1.0


class FormattedResultDTO(BaseModel):
    query_id: str
    execution_result: QueryExecutionResultDTO
    evidence: list[EvidenceReferenceDTO] = []


class ConversationMessageDTO(BaseModel):
    message_id: str
    conversation_id: str
    message_type: str = "ai_response"
    content_text: str = ""
    content_kannada: Optional[str] = None
    sql_text: Optional[str] = None
    query_id: Optional[str] = None
    evidence_refs: list[EvidenceReferenceDTO] = []
    confidence_class: str = "high"
    grounding_status: str = "verified"
    chart_recommendation: Optional[str] = None
    suggested_followups: list[str] = []
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    created_at: Optional[str] = None


class CrimeTrendRequestDTO(BaseModel):
    dimension: str = "month"
    group_by: str = "district"
    district_ids: Optional[list[int]] = None
    crime_sub_head_ids: Optional[list[int]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    include_rolling_avg: bool = True
    include_pct_change: bool = True


class CrimeTrendResultDTO(BaseModel):
    query_id: str
    aggregation: list[dict[str, Any]] = []
    total_records_analyzed: int = 0
    missing_data_pct: float = 0.0
    evidence_refs: list[EvidenceReferenceDTO] = []


class HotspotRequestDTO(BaseModel):
    district_id: int
    crime_sub_head_ids: Optional[list[int]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    eps_km: float = 0.5
    min_cases: int = 5


class HotspotClusterDTO(BaseModel):
    cluster_id: int
    centroid_lat: float
    centroid_lng: float
    case_count: int
    radius_km: float
    crime_type: Optional[str] = None
    case_ids: list[int] = []


class HotspotResultDTO(BaseModel):
    query_id: str
    clusters: list[HotspotClusterDTO] = []
    cases_without_gps: int = 0
    total_cases_analyzed: int = 0
    algorithm: str = "DBSCAN"
    algorithm_params: dict[str, Any] = {}


class SociologicalAnalysisRequestDTO(BaseModel):
    person_type: str = "complainant"
    group_by_fields: list[str] = []
    filters: dict[str, Any] = {}


class SociologicalAnalysisResultDTO(BaseModel):
    query_id: str
    distributions: list[dict[str, Any]] = []
    sample_size: int = 0
    missing_data_pct: float = 0.0
    suppressed_groups: int = 0
    privacy_note: str = ""


class EntityResolutionRequestDTO(BaseModel):
    accused_name: str


class EntityResolutionCandidate(BaseModel):
    candidate_id: str
    accused_master_id: int
    accused_name: str
    case_master_id: int
    age_year: Optional[int] = None
    gender_id: Optional[int] = None
    match_type: str = "unresolved_possible"
    match_score: float = 0.0
    match_features: dict[str, Any] = {}


class EntityResolutionResultDTO(BaseModel):
    query_id: str
    search_name: str
    candidates: list[EntityResolutionCandidate] = []
    resolution_note: str = ""


class GraphNodeDTO(BaseModel):
    id: str
    label: str
    node_type: str = "accused"
    cases: int = 0
    risk_tier: Optional[str] = None


class GraphEdgeDTO(BaseModel):
    id: str
    source: str
    target: str
    weight: int = 1
    shared_cases: list[int] = []
    evidence: list[dict[str, Any]] = []


class GraphProjectionDTO(BaseModel):
    run_id: str
    center_node: str
    nodes: list[GraphNodeDTO] = []
    edges: list[GraphEdgeDTO] = []
    max_depth: int = 2
    node_limit: int = 50
    edge_limit: int = 100
    entity_resolution_note: str = ""


class GraphAnalyticsResultDTO(BaseModel):
    run_id: str
    communities: list[dict[str, Any]] = []
    centrality: dict[str, Any] = {}
    community_note: str = ""


class OffenderProfileDTO(BaseModel):
    entity_id: str
    canonical_name: str
    name_variants: list[str] = []
    age_range: Optional[dict[str, Any]] = None
    gender: Optional[str] = None
    case_count: int = 0
    linked_cases: list[dict[str, Any]] = []
    resolution_confidence: str = "medium"
    priority_score: Optional[dict[str, Any]] = None


class PriorityScoreFeature(BaseModel):
    feature_id: str
    name: str
    raw_value: str
    normalized_value: float
    weight: float
    contribution: float
    is_missing: bool = False


class PriorityScoreDTO(BaseModel):
    execution_id: str
    entity_id: str
    entity_name: str
    score_version: str = "1.0.0"
    total_score: float = 0.0
    risk_tier: str = "LOW"
    max_possible_score: float = 100.0
    features: list[PriorityScoreFeature] = []
    missing_features: list[str] = []
    disclaimer: str = ""
    computed_at: str = ""


class CaseSummaryDTO(BaseModel):
    case_master_id: int
    crime_no: Optional[str] = None
    crime_registered_date: Optional[str] = None
    brief_facts_summary: Optional[str] = None
    crime_category: Optional[str] = None
    gravity_offence: Optional[str] = None
    crime_head: Optional[str] = None
    crime_sub_head: Optional[str] = None
    case_status: Optional[str] = None
    police_station: Optional[str] = None
    district: Optional[str] = None
    evidence_refs: list[EvidenceReferenceDTO] = []


class TimelineEventDTO(BaseModel):
    event_id: str
    event_type: str
    event_date: Optional[str] = None
    description: str
    source_table: str
    source_record_id: int


class SimilarCaseDTO(BaseModel):
    case_master_id: int
    similarity_score: float
    crime_no: Optional[str] = None
    crime_sub_head: Optional[str] = None
    crime_registered_date: Optional[str] = None
    district_name: Optional[str] = None
    per_feature_scores: dict[str, float] = {}


class InvestigativeLeadDTO(BaseModel):
    lead_id: str
    case_master_id: int
    lead_type: str
    lead_description: str
    confidence_class: str
    confidence_score: float
    supporting_evidence: list[dict[str, Any]] = []


class ForecastRequestDTO(BaseModel):
    district_id: int
    crime_sub_head_id: int
    training_window_days: int = 365
    forecast_horizon_days: int = 30


class ForecastDataPoint(BaseModel):
    date: str
    predicted: float
    lower: float
    upper: float


class ForecastResultDTO(BaseModel):
    run_id: str
    model: str = "Prophet v1.0"
    district: str = ""
    crime_type: str = ""
    training_days: int = 0
    horizon_days: int = 0
    metrics: dict[str, Any] = {}
    forecast: list[ForecastDataPoint] = []
    evidence_refs: list[EvidenceReferenceDTO] = []


class EarlyWarningAlertDTO(BaseModel):
    alert_id: str
    rule_id: str
    alert_type: str
    severity: str = "warning"
    title: str
    description: str
    triggering_condition: str
    district_id: Optional[int] = None
    evidence: list[dict[str, Any]] = []
    created_at: str = ""


class DashboardStatsDTO(BaseModel):
    total_cases: int = 0
    heinous_pct: float = 0.0
    pending_cases: int = 0
    district_count: int = 0
    station_count: int = 0


class FinancialAnalysisResultDTO(BaseModel):
    data_available: bool = False
    schema_source: str = "KSP FIR Schema"
    missing_datasets: list[str] = []
    message: str = ""
    synthetic_demo_available: bool = True
    synthetic_data_label: str = "DEMONSTRATION DATA ONLY - NOT REAL KSP RECORDS"


class AuditEventDTO(BaseModel):
    audit_id: str
    timestamp: str
    trace_id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    outcome: str
    error_code: Optional[str] = None
    client_ip: Optional[str] = None
    request_duration_ms: Optional[int] = None


class FeedbackDTO(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ConversationDTO(BaseModel):
    conversation_id: str
    title: str
    language_code: str = "en"
    created_at: str = ""
    is_archived: bool = False


class InvestigationDTO(BaseModel):
    investigation_id: str
    title: str
    description: Optional[str] = None
    status: str = "active"
    created_at: str = ""
    case_count: int = 0
    query_count: int = 0


class SavedGraphDTO(BaseModel):
    saved_graph_id: str
    label: str
    center_node_name: Optional[str] = None
    node_count: int = 0
    edge_count: int = 0
    created_at: str = ""


class ReportJobDTO(BaseModel):
    job_id: str
    status: str = "pending"
    stratus_url: Optional[str] = None
    created_at: str = ""


class AuditLogEntryDTO(BaseModel):
    entry_id: str
    timestamp: str
    event_type: str
    category: str = "system"
    actor_kgid: str = "system"
    actor_role: str = "system"
    resource_type: str = ""
    resource_id: str = ""
    detail: str = ""
    result: str = "success"


class HealthCheckDTO(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
