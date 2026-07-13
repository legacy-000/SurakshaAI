from typing import Any, Optional
from pydantic import BaseModel
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


class QueryRequestDTO(BaseModel):
    message: str
    lang: str = "en"
    conversation_id: Optional[str] = None


class EvidenceReferenceDTO(BaseModel):
    evidence_id: str
    evidence_type: str = "database_fact"
    source_table: Optional[str] = None
    source_record_count: Optional[int] = None
    filter_summary: Optional[str] = None
    display_label: Optional[str] = None
    confidence: float = 1.0


class ConversationMessageDTO(BaseModel):
    message_id: str
    conversation_id: str = ""
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
    query_id: str = ""
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
    query_id: str = ""
    clusters: list[HotspotClusterDTO] = []
    cases_without_gps: int = 0
    total_cases_analyzed: int = 0
    algorithm: str = "DBSCAN"
    algorithm_params: dict[str, Any] = {}


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
    feature_id: str = ""
    name: str
    raw_value: str
    normalized_value: float
    weight: float
    contribution: float
    is_missing: bool = False


class PriorityScoreDTO(BaseModel):
    execution_id: str = ""
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
    run_id: str = ""
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
    alert_type: str = ""
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
