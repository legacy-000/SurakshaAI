export interface User {
  user_id: string;
  kgid: string;
  first_name: string;
  role_id: number;
  role_name: string;
  unit_id?: number;
  district_id?: number;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface EvidenceRef {
  evidence_id: string;
  evidence_type: string;
  source_table?: string;
  source_record_count?: number;
  display_label?: string;
}

export interface ChatMessage {
  message_id: string;
  message_type: 'user_query' | 'ai_response';
  content_text: string;
  content_kannada?: string;
  sql_text?: string;
  evidence_refs?: EvidenceRef[];
  chart_recommendation?: string;
  suggested_followups?: string[];
  data_quality_warnings?: string[];
  tool_params?: Record<string, any>;
  confidence_class?: string;
  grounding_status?: string;
  created_at: string;
}

export interface PriorityScoreFeature {
  name: string;
  raw_value: string;
  normalized_value: number;
  weight: number;
  contribution: number;
  is_missing?: boolean;
}

export interface PriorityScore {
  total_score: number;
  risk_tier: 'LOW' | 'MODERATE' | 'ELEVATED' | 'HIGH';
  score_version: string;
  features: PriorityScoreFeature[];
  disclaimer: string;
}

export interface OffenderProfile {
  entity_name: string;
  total_score: number;
  risk_tier: string;
  features: PriorityScoreFeature[];
  linked_cases: LinkedCase[];
  disclaimer: string;
}

export interface LinkedCase {
  case_id: number;
  crime_no: string;
  crime_type: string;
  year: number;
  status: string;
}

export interface TrendDataPoint {
  period: string;
  count: number;
  pct_change?: number;
  crime_type?: string;
}

export interface HotspotCluster {
  cluster_id: number;
  centroid_lat: number;
  centroid_lng: number;
  case_count: number;
  radius_km: number;
  crime_type: string;
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  cases: number;
  risk_tier?: string;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  shared_cases: number[];
}

export interface Conversation {
  conversation_id: string;
  title: string;
  messages: ChatMessage[];
}

export interface ForecastDataPoint {
  date: string;
  predicted: number;
  upper: number;
  lower: number;
  actual?: number;
  category?: string;
  district?: string;
}

export interface Investigation {
  investigation_id: string;
  title: string;
  description?: string;
  status: string;
  created_at: string;
  case_count: number;
  query_count: number;
  cases?: { case_master_id: number; notes: string }[];
  queries?: { query_id: string }[];
  graphs?: SavedGraph[];
}

export interface SavedGraph {
  saved_graph_id: string;
  label: string;
  node_count: number;
  edge_count: number;
  created_at: string;
}

export interface SimilarCase {
  case_master_id: number;
  similarity_score: number;
  crime_no?: string;
  crime_sub_head?: string;
  crime_registered_date?: string;
  district_name?: string;
  per_feature_scores?: Record<string, number>;
}

export interface InvestigativeLead {
  lead_id: string;
  case_master_id: number;
  lead_type: string;
  lead_description: string;
  confidence_class: string;
  confidence_score: number;
  supporting_evidence?: { evidence_type: string; source_table: string; evidence_description: string }[];
}

export interface TimelineEvent {
  event_id: string;
  event_type: string;
  event_date?: string;
  description: string;
  source_table: string;
  source_record_id: number;
}

// ── Phase 5 — AI Governance ───────────────────────────────────────────
export interface ModelRegistryEntry {
  model_id: string;
  model_name: string;
  model_version: string;
  provider: string;
  capabilities: string[];
  parameters: Record<string, any>;
  created_at: string;
}

export interface PromptRegistryEntry {
  prompt_id: string;
  prompt_name: string;
  prompt_version: string;
  prompt_text: string;
  model_id?: string;
  created_at: string;
}

export interface AgentCapability {
  agent_name: string;
  intents: string[];
  description: string;
  required_permissions: string[];
}

export interface AgentExecution {
  execution_id: string;
  mission_id: string;
  agent_name: string;
  intent: string;
  input_query: string;
  output_summary: string;
  evidence_ids: string[];
  status: string;
  started_at: string;
  completed_at?: string;
}

export interface Mission {
  mission_id: string;
  query: string;
  user_id: string;
  intents: Record<string, any>;
  status: string;
  summary: string;
  created_at: string;
  completed_at?: string;
}

export interface MissionTask {
  task_id: string;
  mission_id: string;
  agent_name: string;
  intent: string;
  input_query: string;
  status: string;
  result?: any;
  evidence: { evidence_id: string; evidence_type: string; source_table?: string }[];
  started_at: string;
  completed_at?: string;
  error?: string;
}

export interface ClaimEntry {
  claim_id: string;
  statement: string;
  classification: string;
  producer: string;
  model_version?: string;
  evidence_refs: string[];
  confidence: number;
  confidence_label: string;
  validation_status: string;
  created_at: string;
  source_execution_id?: string;
}

// ── Communication & Resource Sharing ─────────────────────────────────
export interface MessageAttachment {
  file_id: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
}

export interface MessageSender {
  employee_id: number;
  rank: string;
  unit?: { unit_id: number; unit_name: string };
}

export interface MessageRecipient {
  employee_id: number;
  status: string;
  delivered_at?: string;
  read_at?: string;
}

export interface Message {
  message_id: string;
  type: string;
  sender: MessageSender;
  recipients: MessageRecipient[];
  cc: MessageRecipient[];
  subject: string;
  body: string;
  linked_resources: { resourceType?: string; resourceId?: number }[];
  attachments: MessageAttachment[];
  priority: string;
  status: string;
  created_at: string;
  sent_at?: string;
  parent_message_id?: string;
  thread_id?: string;
}

export interface PermissionCheck {
  resource_type: string;
  resource_id?: number;
  action: string;
  allowed: boolean;
  denial_reason: string;
}

export interface TempPermission {
  permission_id: string;
  grantor_employee_id: number;
  grantee_employee_id: number;
  permission: string;
  scope: string;
  valid_from: string;
  valid_until: string;
  reason: string;
  status: string;
}

export interface DynamicGroup {
  group_id: string;
  group_name: string;
  group_type: string;
  description?: string;
  lead_employee_id: number;
  linked_case_ids: number[];
  linked_offender_ids: number[];
  dissolve_at?: string;
  status: string;
  created_at: string;
}

export interface GroupMember {
  employee_id: number;
  rank?: string;
  name?: string;
  unit?: string;
  role_in_group: string;
  joined_at?: string;
}

export interface CoordinationRequest {
  request_id: string;
  request_type: string;
  priority: string;
  description: string;
  from_employee_id: number;
  requesting_unit_id?: number;
  target_unit_id: number;
  linked_case_ids: number[];
  status: string;
  created_at: string;
  responded_at?: string;
  responded_by?: number;
  responding_unit_id?: number;
}

export interface AuditLogEntry {
  entry_id: string;
  timestamp: string;
  event_type: string;
  category: string;
  actor_kgid: string;
  actor_role: string;
  resource_type: string;
  resource_id: string;
  detail: string;
  result: string;
}
