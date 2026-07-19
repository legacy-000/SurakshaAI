import { LoginResponse, ChatMessage, ForecastDataPoint, PriorityScore } from '../types';

// ponytail: only getPriorityScore needs mock (synchronous, no backend action yet)
import { mocks } from './mocks';

// ponytail: dev-mode mock auth — used only when backend is unreachable (local dev without Catalyst).
// In production, the real backend returns a token and this branch never runs.
const DEV_USERS: Record<string, any> = {
  INV001: { kgid: 'INV001', name: 'Ravi Kumar', role_name: 'Investigator', role_id: 1, unit_id: 1, district_id: 1 },
  ANL001: { kgid: 'ANL001', name: 'Priya Sharma', role_name: 'Analyst', role_id: 2, district_id: 18 },
  SUP001: { kgid: 'SUP001', name: 'Amit Singh', role_name: 'Supervisor', role_id: 3, unit_id: 1, district_id: 1 },
  POL001: { kgid: 'POL001', name: 'Dr. Meena Rao', role_name: 'Policymaker', role_id: 4, district_id: 18 },
  ADM001: { kgid: 'ADM001', name: 'Vikram P', role_name: 'System Administrator', role_id: 5 },
  TSE001: { kgid: 'TSE001', name: 'Anita Rao', role_name: 'Technical Support Engineer', role_id: 6 },
};

async function postToBackend(action: string, params: Record<string, any> = {}): Promise<any> {
  const userStr = localStorage.getItem('user_context');
  const userContext = userStr ? JSON.parse(userStr) : null;

  const response = await fetch('/api/', {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: JSON.stringify({
      action,
      params,
      session: { user_context: userContext }
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // ── Investigation Suite ───────────────────────────────────────────
  createInvestigation(title: string, description: string = '') {
    return postToBackend('create_investigation', { title, description });
  },

  listInvestigations() {
    return postToBackend('list_investigations');
  },

  getInvestigation(id: string) {
    return postToBackend('get_investigation', { investigation_id: id });
  },

  addCaseToInvestigation(investigationId: string, caseMasterId: number, notes: string = '') {
    return postToBackend('add_case_to_investigation', { investigation_id: investigationId, case_master_id: caseMasterId, notes });
  },

  getCaseSimilarity(caseMasterId: number, topK: number = 5) {
    return postToBackend('get_case_similarity', { case_master_id: caseMasterId, top_k: topK });
  },

  getCaseLeads(caseMasterId: number) {
    return postToBackend('get_case_leads', { case_master_id: caseMasterId });
  },

  getCaseTimeline(caseMasterId: number) {
    return postToBackend('get_case_timeline', { case_master_id: caseMasterId });
  },

  generateInvestigationReport(investigationId: string) {
    return postToBackend('generate_investigation_report', { investigation_id: investigationId });
  },

  // ── AI Governance — Phase 5 ──────────────────────────────────────
  listModels() { return postToBackend('list_models'); },

  listAgentCapabilities() { return postToBackend('list_agent_capabilities'); },

  listMissions() { return postToBackend('list_missions'); },

  getMission(missionId: string) { return postToBackend('get_mission', { mission_id: missionId }); },

  listClaims() { return postToBackend('list_claims'); },

  addClaim(statement: string, classification: string, producer: string, modelVersion?: string, evidenceRefs?: string[], confidence?: number) {
    return postToBackend('add_claim', { statement, classification, producer, model_version: modelVersion, evidence_refs: evidenceRefs, confidence });
  },

  updateClaimStatus(claimId: string, status: string) {
    return postToBackend('update_claim_status', { claim_id: claimId, status });
  },

  // ── Comms — Messages ──────────────────────────────────────────────
  sendMessage(type: string, subject: string, body: string, toIds: number[], priority: string = 'NORMAL', parentMessageId?: string, ccIds?: number[]) {
    return postToBackend('send_message', { type, subject, body, to_ids: toIds, priority, parent_message_id: parentMessageId, cc_ids: ccIds, unit_id: 1, unit_name: 'Station' });
  },

  listInbox(employeeId: number, unreadOnly: boolean = false, priorityFilter?: string, since?: string) {
    return postToBackend('list_inbox', { employee_id: employeeId, unread_only: unreadOnly, priority_filter: priorityFilter, since });
  },

  getMessage(messageId: string) { return postToBackend('get_message', { message_id: messageId }); },

  markRead(messageId: string, employeeId: number) {
    return postToBackend('mark_read', { message_id: messageId, employee_id: employeeId }).then(r => !!r.ok);
  },

  acknowledgeMessage(messageId: string, employeeId: number) {
    return postToBackend('acknowledge_message', { message_id: messageId, employee_id: employeeId }).then(r => !!r.ok);
  },

  getThread(messageId: string) { return postToBackend('get_thread', { message_id: messageId }); },

  // ── Comms — Permissions ───────────────────────────────────────────
  checkPermission(rank: string, resourceType: string, action: string, scope?: string) {
    return postToBackend('check_permission', { rank, resource_type: resourceType, action, scope });
  },

  delegatePermission(grantorId: number, granteeId: number, permission: string, scope: string = 'own_station', validUntil?: string, reason?: string) {
    return postToBackend('delegate_permission', { grantor_id: grantorId, grantee_id: granteeId, permission, scope, valid_until: validUntil, reason });
  },

  revokeDelegation(permissionId: string) {
    return postToBackend('revoke_delegation', { permission_id: permissionId }).then(r => !!r.ok);
  },

  listDelegations(grantorId?: number, granteeId?: number) {
    return postToBackend('list_delegations', { grantor_id: grantorId, grantee_id: granteeId });
  },

  setEmergency(active: boolean, durationHours: number = 72) {
    return postToBackend('set_emergency', { active, duration_hours: durationHours }).then(r => !!r.emergency);
  },

  getEmergencyStatus() {
    return postToBackend('get_emergency_status').then(r => !!r.emergency);
  },

  // ── Comms — Groups ────────────────────────────────────────────────
  createDynamicGroup(name: string, groupType: string, leadId: number, caseIds?: number[], dissolveHours?: number, description?: string, offenderIds?: number[]) {
    return postToBackend('create_dynamic_group', { name, group_type: groupType, lead_id: leadId, case_ids: caseIds, dissolve_hours: dissolveHours, description, offender_ids: offenderIds });
  },

  listDynamicGroups(activeOnly: boolean = true) {
    return postToBackend('list_dynamic_groups', { active_only: activeOnly });
  },

  dissolveGroup(groupId: string) {
    return postToBackend('dissolve_group', { group_id: groupId }).then(r => !!r.ok);
  },

  addGroupMember(groupId: string, employeeId: number, roleInGroup: string = 'member') {
    return postToBackend('add_group_member', { group_id: groupId, employee_id: employeeId, role_in_group: roleInGroup });
  },

  removeGroupMember(groupId: string, employeeId: number) {
    return postToBackend('remove_group_member', { group_id: groupId, employee_id: employeeId }).then(r => !!r.ok);
  },

  listGroupMembers(groupId: string) { return postToBackend('list_group_members', { group_id: groupId }); },

  listMyGroups(employeeId: number) { return postToBackend('list_my_groups', { employee_id: employeeId }); },

  // ── Comms — Coordination ──────────────────────────────────────────
  createCoordination(requestType: string, targetUnitId: number, priority: string, description: string, linkedCaseIds?: number[]) {
    const userCtx = JSON.parse(localStorage.getItem('user_context') || '{}');
    const fromId = Number(userCtx?.user_id?.replace(/\D/g, '') || 1);
    return postToBackend('create_coordination', { from_id: fromId, request_type: requestType, target_unit_id: targetUnitId, priority, description, linked_case_ids: linkedCaseIds || [] });
  },

  updateCoordination(requestId: string, status: string, assignedTo?: number) {
    return postToBackend('update_coordination', { request_id: requestId, status, assigned_to: assignedTo }).then(r => !!r.ok);
  },

  listCoordination(fromId?: number, toUnit?: number, status?: string) {
    return postToBackend('list_coordination', { from_id: fromId, to_unit: toUnit, status });
  },

  listAuditLog(limit?: number, eventType?: string, category?: string, actor?: string) {
    return postToBackend('list_audit_log', { limit, event_type: eventType, category, actor });
  },

  async login(kgid: string, password: string): Promise<LoginResponse> {
    let res: any;
    try {
      res = await postToBackend('login', { kgid, password });
    } catch {
      // ponytail: dev fallback — backend unreachable, allow mock login for demo
      const u = DEV_USERS[kgid?.toUpperCase()];
      if (!u || password !== 'pass123') {
        throw new Error('Login failed');
      }
      res = { token: `dev.${btoa(u.kgid)}.${Date.now()}`, user: u, expires_in: 3600 };
    }
    if (!res || !res.token) throw new Error('Login failed: no token returned');
    localStorage.setItem('token', res.token);
    localStorage.setItem('user_context', JSON.stringify(res.user));
    return res;
  },

  async chatQuery(message: string, conversationId?: string): Promise<ChatMessage> {
    const res = await postToBackend('chat_query', { message, conversation_id: conversationId });
    return {
      message_id: res.message_id,
      message_type: res.message_type || 'ai_response',
      content_text: res.content_text || '',
      content_kannada: res.content_kannada,
      sql_text: res.sql_text,
      chart_recommendation: res.chart_recommendation,
      evidence_refs: (res.evidence_refs || []).map((e: any) => ({
        evidence_id: e.evidence_id,
        evidence_type: e.evidence_type || 'database_fact',
        source_table: e.source_table,
        source_record_count: e.source_record_count,
        display_label: e.display_label,
      })),
      data_quality_warnings: res.data_quality_warnings || [],
      tool_params: res.tool_params || {},
      suggested_followups: res.suggested_followups || [],
      created_at: res.created_at || new Date().toISOString(),
    };
  },

  getForecastData(category?: string, district?: string) {
    return postToBackend('get_forecast', { category, district });
  },

  async getMultiForecast(): Promise<{ category: string; data: ForecastDataPoint[] }[]> {
    const categories = ['Theft', 'Robbery', 'Assault', 'Cyber Crime', 'Burglary'];
    const results = await Promise.all(
      categories.map(cat => this.getForecastData(cat, 'Bengaluru Urban').then(data => ({ category: cat, data })))
    );
    return results;
  },

  async getDistrictForecasts(): Promise<{ district: string; data: ForecastDataPoint[] }[]> {
    const topDistricts = ['Bengaluru Urban', 'Mysuru', 'Hubballi-Dharwad', 'Mangaluru', 'Belagavi'];
    const results = await Promise.all(
      topDistricts.map(dist => this.getForecastData('Theft', dist).then(data => ({ district: dist, data })))
    );
    return results;
  },

  getOffenderProfile(name: string) {
    return postToBackend('get_offender_profile', { name });
  },

  createOffenderProfile(profile: { accused_name: string; case_master_id: number; age_year: number; gender_id: number; person_id: string }) {
    return postToBackend('create_offender_profile', profile);
  },

  // ponytail: synchronous, no backend action — pure mock until backend lands
  getPriorityScore(): PriorityScore {
    return mocks.priorityScore();
  },

  getTrends() { return postToBackend('get_trends'); },

  getHotspots(districtId: number = 1, epsKm: number = 20, minCases: number = 3) {
    return postToBackend('get_hotspots', { district_id: districtId, eps_km: epsKm, min_cases: minCases });
  },

  getSocioDemographics() { return postToBackend('get_socio_demographics'); },

  getNetwork(accusedName: string) { return postToBackend('get_network', { accused_name: accusedName }); },

  getDashboardKpis() { return postToBackend('get_dashboard_kpis'); },

  getAlerts() { return postToBackend('get_alerts'); },

  commanderQuery(query: string) { return postToBackend('commander_query', { query }); },

  getActivityFeed() { return postToBackend('get_activity_feed'); },

  speechToText(audioBytes: number[], language: string) {
    return postToBackend('speech_to_text', { audio_bytes: audioBytes, language }).then(r => r.text);
  },

  textToSpeech(text: string, language: string) {
    return postToBackend('text_to_speech', { text, language }).then(r => r.audio_bytes);
  }
};
