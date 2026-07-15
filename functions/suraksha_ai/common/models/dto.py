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
    data_quality_warnings: list[str] = []
    tool_params: dict = {}
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


# ── Phase 5 — AI Governance ──────────────────────────────────────────

class ModelRegistryEntryDTO(BaseModel):
    model_id: str
    model_name: str
    model_version: str
    provider: str = ""
    capabilities: list[str] = []
    parameters: dict[str, Any] = {}
    created_at: str = ""


class PromptRegistryEntryDTO(BaseModel):
    prompt_id: str
    prompt_name: str
    prompt_version: str
    prompt_text: str
    model_id: Optional[str] = None
    created_at: str = ""


class AgentCapabilityDTO(BaseModel):
    agent_name: str
    intents: list[str]
    description: str = ""
    required_permissions: list[str] = []


class AgentExecutionDTO(BaseModel):
    execution_id: str
    mission_id: str
    agent_name: str
    intent: str = ""
    input_query: str = ""
    output_summary: str = ""
    evidence_ids: list[str] = []
    status: str = "pending"
    started_at: str = ""
    completed_at: Optional[str] = None


class AgentResultEnvelopeDTO(BaseModel):
    execution_id: str
    agent_name: str
    status: str
    data: Any = None
    evidence: list[EvidenceReferenceDTO] = []
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class MissionDTO(BaseModel):
    mission_id: str
    query: str = ""
    user_id: str = ""
    intents: dict[str, Any] = {}
    status: str = "created"
    summary: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None


class MissionTaskDTO(BaseModel):
    task_id: str
    mission_id: str
    agent_name: str
    intent: str = ""
    input_query: str = ""
    status: str = "pending"
    result: Any = None
    evidence: list[EvidenceReferenceDTO] = []
    started_at: str = ""
    completed_at: Optional[str] = None
    error: Optional[str] = None


class ClaimLedgerEntryDTO(BaseModel):
    claim_id: str
    statement: str
    classification: str = "DATABASE_FACT"
    producer: str = ""
    model_version: Optional[str] = None
    evidence_refs: list[str] = []
    confidence: float = 1.0
    confidence_label: str = "high"
    validation_status: str = "Under Review"
    created_at: str = ""
    source_execution_id: Optional[str] = None


# ── Communication & Resource Sharing ─────────────────────────────────

class MessageAttachmentDTO(BaseModel):
    file_id: str
    file_name: str
    mime_type: str = "application/octet-stream"
    size_bytes: int = 0


class OrgUnitDTO(BaseModel):
    unit_id: int
    unit_name: str = ""


class MessageSenderDTO(BaseModel):
    employee_id: int
    rank: str = ""
    unit: Optional[OrgUnitDTO] = None


class MessageRecipientStatus(BaseModel):
    employee_id: int
    status: str = "pending"
    delivered_at: Optional[str] = None
    read_at: Optional[str] = None


class MessageDTO(BaseModel):
    message_id: str
    type: str = "STATUS_UPDATE"
    sender: MessageSenderDTO
    recipients: list[MessageRecipientStatus] = []
    cc: list[MessageRecipientStatus] = []
    subject: str = ""
    body: str = ""
    linked_resources: list[dict[str, Any]] = []
    attachments: list[MessageAttachmentDTO] = []
    priority: str = "NORMAL"
    status: str = "DRAFT"
    created_at: str = ""
    sent_at: Optional[str] = None
    parent_message_id: Optional[str] = None
    thread_id: Optional[str] = None


class PermissionCheckDTO(BaseModel):
    resource_type: str
    resource_id: Optional[int] = None
    action: str
    allowed: bool = False
    denial_reason: str = ""


class TempPermissionDTO(BaseModel):
    permission_id: str
    grantor_employee_id: int
    grantee_employee_id: int
    permission: str
    scope: str = "own_station"
    valid_from: str = ""
    valid_until: str = ""
    reason: str = ""
    status: str = "active"


class OrgGroupDTO(BaseModel):
    group_id: str
    group_name: str
    group_type: str = "STATION"
    parent_group_id: Optional[str] = None
    created_at: str = ""


class DynamicGroupDTO(BaseModel):
    group_id: str
    group_name: str
    group_type: str = "TASK_FORCE"
    lead_employee_id: int = 0
    linked_case_ids: list[int] = []
    linked_offender_ids: list[int] = []
    dissolve_at: Optional[str] = None
    status: str = "active"
    created_at: str = ""


class DynamicGroupMemberDTO(BaseModel):
    membership_id: str
    group_id: str
    employee_id: int
    role: str = "MEMBER"
    can_modify: bool = False
    can_approve: bool = False
    data_scope: str = "group"


class CoordinationRequestDTO(BaseModel):
    request_id: str
    from_employee_id: int
    to_unit_id: int
    request_type: str = "SUSPECT_LOCATION"
    subject: str = ""
    body: str = ""
    linked_case_id: Optional[int] = None
    status: str = "pending"
    created_at: str = ""
    assigned_to_employee_id: Optional[int] = None


class AuditLogEntryDTO(BaseModel):
    entry_id: str
    timestamp: str
    event_type: str
    category: str = ""
    actor_kgid: str = ""
    actor_role: str = ""
    resource_type: str = ""
    resource_id: str = ""
    detail: str = ""
    result: str = "success"
