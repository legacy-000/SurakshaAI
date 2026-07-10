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
