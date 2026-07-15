import { LoginResponse, ChatMessage, OffenderProfile, TrendDataPoint, HotspotCluster, GraphNode, GraphEdge, PriorityScore, ForecastDataPoint, Investigation, SimilarCase, InvestigativeLead, TimelineEvent, ModelRegistryEntry, AgentCapability, Mission, ClaimEntry, Message, PermissionCheck, TempPermission, DynamicGroup, GroupMember, CoordinationRequest, AuditLogEntry } from '../types';

const MOCK_TOKEN = 'mock_jwt_INV001_1';

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

const users: Record<string, LoginResponse> = {
  INV001: { token: MOCK_TOKEN, user: { user_id: 'INV001', kgid: 'INV001', first_name: 'Ravi Kumar', role_id: 1, role_name: 'Investigator', unit_id: 1, district_id: 1 } },
  ANL001: { token: MOCK_TOKEN, user: { user_id: 'ANL001', kgid: 'ANL001', first_name: 'Priya Sharma', role_id: 2, role_name: 'Analyst', district_id: 18 } },
  SUP001: { token: MOCK_TOKEN, user: { user_id: 'SUP001', kgid: 'SUP001', first_name: 'Amit Singh', role_id: 3, role_name: 'Supervisor', unit_id: 1, district_id: 1 } },
  POL001: { token: MOCK_TOKEN, user: { user_id: 'POL001', kgid: 'POL001', first_name: 'Dr. Meena Rao', role_id: 4, role_name: 'Policymaker', district_id: 18 } },
  ADM001: { token: MOCK_TOKEN, user: { user_id: 'ADM001', kgid: 'ADM001', first_name: 'Vikram P', role_id: 5, role_name: 'System Administrator' } },
};

const accusedNames = [
  'Ravi Kumar', 'Suresh P', 'Rajesh K', 'Manoj R', 'Venkatesh G',
  'Prakash M', 'Kumar S', 'Anil K', 'Sunil D', 'Gopal R',
  'Mahesh N', 'Dinesh B', 'Satish H', 'Vinod T', 'Harish M',
];

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

async function postToBackend(action: string, params: Record<string, any> = {}): Promise<any> {
  const userStr = localStorage.getItem('user_context');
  const userContext = userStr ? JSON.parse(userStr) : null;

  // text/plain avoids CORS preflight (OPTIONS) that Catalyst API Gateway doesn't handle
  const response = await fetch('/api/', {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain' },
    body: JSON.stringify({
      action,
      params,
      session: {
        user_context: userContext
      }
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // ── Investigation Suite ───────────────────────────────────────────
  async createInvestigation(title: string, description: string = ''): Promise<Investigation> {
    try {
      return await postToBackend('create_investigation', { title, description });
    } catch (e) {
      console.warn("Failed live createInvestigation, using fallback mock.", e);
    }
    await delay(300);
    return {
      investigation_id: 'mock-inv-' + Math.random().toString(36).slice(2, 8),
      title, description, status: 'open', created_at: new Date().toISOString(),
      case_count: 0, query_count: 0, cases: [], queries: [], graphs: [],
    };
  },

  async listInvestigations(): Promise<Investigation[]> {
    try {
      return await postToBackend('list_investigations');
    } catch (e) {
      console.warn("Failed live listInvestigations, using fallback mock.", e);
    }
    return [
      { investigation_id: 'inv-1', title: 'KG Halli Theft Ring', description: 'Link analysis for gang involved in 5 thefts', status: 'open', created_at: '2026-06-01T10:00:00Z', case_count: 3, query_count: 7 },
      { investigation_id: 'inv-2', title: 'Whitefield Robbery Network', description: 'Tracking organized robbery group', status: 'active', created_at: '2026-06-10T14:30:00Z', case_count: 5, query_count: 12 },
    ];
  },

  async getInvestigation(id: string): Promise<Investigation> {
    try {
      return await postToBackend('get_investigation', { investigation_id: id });
    } catch (e) {
      console.warn("Failed live getInvestigation, using fallback mock.", e);
    }
    return {
      investigation_id: id, title: 'Mock Investigation', status: 'open', created_at: '2026-06-01T10:00:00Z',
      case_count: 2, query_count: 5,
      cases: [{ case_master_id: 101, notes: 'Primary case — theft at KG Halli' }, { case_master_id: 204, notes: 'Related robbery case' }],
    };
  },

  async addCaseToInvestigation(investigationId: string, caseMasterId: number, notes: string = ''): Promise<any> {
    try {
      return await postToBackend('add_case_to_investigation', { investigation_id: investigationId, case_master_id: caseMasterId, notes });
    } catch (e) {
      console.warn("Failed live addCaseToInvestigation, using fallback mock.", e);
    }
    return { status: 'ok' };
  },

  async getCaseSimilarity(caseMasterId: number, topK: number = 5): Promise<SimilarCase[]> {
    try {
      return await postToBackend('get_case_similarity', { case_master_id: caseMasterId, top_k: topK });
    } catch (e) {
      console.warn("Failed live getCaseSimilarity, using fallback mock.", e);
    }
    await delay(300);
    const types = ['Theft', 'Robbery', 'Assault', 'Burglary', 'Murder'];
    const dists = ['Bangalore', 'Mysuru', 'Hubli', 'Mangalore'];
    return Array.from({ length: topK }, (_, i) => ({
      case_master_id: 100000 + caseMasterId * 10 + i * 7,
      similarity_score: 0.85 - i * 0.08,
      crime_no: `CN2025${(caseMasterId + i * 13) % 10000}`,
      crime_sub_head: types[i % 5],
      crime_registered_date: `2025-${(i + 2) * 2}-${10 + i * 5}`,
      district_name: dists[i % 4],
      per_feature_scores: { crime_type: 0.9 - i * 0.05, time_proximity: 0.8 - i * 0.07, location: 0.7 - i * 0.06, text_embedding: 0.85 - i * 0.04 },
    }));
  },

  async getCaseLeads(caseMasterId: number): Promise<InvestigativeLead[]> {
    try {
      return await postToBackend('get_case_leads', { case_master_id: caseMasterId });
    } catch (e) {
      console.warn("Failed live getCaseLeads, using fallback mock.", e);
    }
    await delay(300);
    return [
      { lead_id: 'l1', case_master_id: caseMasterId, lead_type: 'co_accused_link', lead_description: `Co-accused linked to ${3 + caseMasterId % 5} prior cases`, confidence_class: 'medium', confidence_score: 0.78, supporting_evidence: [{ evidence_type: 'computed_metric', source_table: 'Accused', evidence_description: 'Accused appears in prior cases' }] },
      { lead_id: 'l2', case_master_id: caseMasterId, lead_type: 'location_pattern', lead_description: `Within 500m of ${2 + caseMasterId % 4} prior incidents`, confidence_class: 'medium', confidence_score: 0.65, supporting_evidence: [{ evidence_type: 'computed_metric', source_table: 'CaseMaster', evidence_description: 'GPS proximity match' }] },
      { lead_id: 'l3', case_master_id: caseMasterId, lead_type: 'witness_lead', lead_description: `Witness W${caseMasterId % 10 + 1} may have additional info`, confidence_class: 'low', confidence_score: 0.42, supporting_evidence: [{ evidence_type: 'database_fact', source_table: 'Witness', evidence_description: 'Witness recorded' }] },
    ];
  },

  async getCaseTimeline(caseMasterId: number): Promise<TimelineEvent[]> {
    try {
      return await postToBackend('get_case_timeline', { case_master_id: caseMasterId });
    } catch (e) {
      console.warn("Failed live getCaseTimeline, using fallback mock.", e);
    }
    const m = Math.max(1, caseMasterId % 12);
    const d = Math.max(1, caseMasterId % 28);
    return [
      { event_id: `ev_${caseMasterId}_reg`, event_type: 'crime_registration', event_date: `2025-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`, description: 'FIR registered', source_table: 'CaseMaster', source_record_id: caseMasterId },
      { event_id: `ev_${caseMasterId}_arr`, event_type: 'arrest', event_date: `2025-${String(Math.min(m + 1, 12)).padStart(2, '0')}-${String(d).padStart(2, '0')}`, description: 'Primary accused arrested', source_table: 'ArrestSurrender', source_record_id: caseMasterId },
      { event_id: `ev_${caseMasterId}_chg`, event_type: 'chargesheet', event_date: `2025-${String(Math.min(m + 3, 12)).padStart(2, '0')}-${String(d).padStart(2, '0')}`, description: 'Chargesheet filed', source_table: 'ChargesheetDetails', source_record_id: caseMasterId },
    ];
  },

  async generateInvestigationReport(investigationId: string): Promise<{ job_id: string; status: string; stratus_url?: string; created_at: string }> {
    try {
      return await postToBackend('generate_investigation_report', { investigation_id: investigationId });
    } catch (e) {
      console.warn("Failed live generateInvestigationReport, using fallback mock.", e);
    }
    return { job_id: 'report-job-1', status: 'completed', stratus_url: `/export/report_${investigationId.slice(0, 8)}.pdf`, created_at: new Date().toISOString() };
  },

  // ── AI Governance — Phase 5 ──────────────────────────────────────
  async listModels(): Promise<ModelRegistryEntry[]> {
    try { return await postToBackend('list_models'); } catch { /* fallback */ }
    return [
      { model_id: 'm1', model_name: 'GLM', model_version: 'crm-di-glm47b_30b_it', provider: 'Zoho', capabilities: ['tool_calling', 'sql_generation'], parameters: {}, created_at: '2026-06-01T00:00:00Z' },
      { model_id: 'm2', model_name: 'Prophet', model_version: '1.1.5', provider: 'Meta', capabilities: ['time_series_forecast'], parameters: {}, created_at: '2026-06-01T00:00:00Z' },
    ];
  },

  async listAgentCapabilities(): Promise<AgentCapability[]> {
    try { return await postToBackend('list_agent_capabilities'); } catch { /* fallback */ }
    return [
      { agent_name: 'database_query', intents: ['database_query', 'case_lookup'], description: 'Query FIR database', required_permissions: ['chat_query'] },
      { agent_name: 'trend_analysis', intents: ['trend_analysis'], description: 'Analyze crime trends', required_permissions: ['view_trends'] },
    ];
  },

  async listMissions(): Promise<Mission[]> {
    try { return await postToBackend('list_missions'); } catch { /* fallback */ }
    return [];
  },

  async getMission(missionId: string): Promise<{ mission: Mission; tasks: any[] }> {
    try { return await postToBackend('get_mission', { mission_id: missionId }); } catch { /* fallback */ }
    return { mission: { mission_id: missionId, query: '', user_id: '', intents: {}, status: 'unknown', summary: '', created_at: '' }, tasks: [] };
  },

  async listClaims(): Promise<ClaimEntry[]> {
    try { return await postToBackend('list_claims'); } catch { /* fallback */ }
    return [
      { claim_id: 'c1', statement: 'FIR registered on 2026-03-15', classification: 'DATABASE_FACT', producer: 'CaseMaster', evidence_refs: ['CaseMaster:10443'], confidence: 1.0, confidence_label: 'high', validation_status: 'Accepted', created_at: '2026-06-01T00:00:00Z' },
      { claim_id: 'c2', statement: 'Location within 500m of 2 prior cases', classification: 'COMPUTED_FINDING', producer: 'Geospatial Agent', model_version: 'v1.2', evidence_refs: ['CaseMaster:10443', 'Hotspot:cluster_3'], confidence: 0.89, confidence_label: 'high', validation_status: 'Under Review', created_at: '2026-06-01T00:00:00Z' },
      { claim_id: 'c3', statement: 'Offender has ELEVATED recidivism risk', classification: 'MODEL_PREDICTION', producer: 'Priority Score Engine', model_version: '1.0.0', evidence_refs: ['PriorityScore:INV001'], confidence: 0.76, confidence_label: 'medium', validation_status: 'Under Review', created_at: '2026-06-01T00:00:00Z' },
      { claim_id: 'c4', statement: 'Unknown third party may be involved', classification: 'MODEL_HYPOTHESIS', producer: 'InvestigationAI', model_version: 'claude-sonnet-4-6', evidence_refs: ['Evidence:missing_report'], confidence: 0.35, confidence_label: 'low', validation_status: 'Disputed', created_at: '2026-06-01T00:00:00Z' },
    ];
  },

  async addClaim(statement: string, classification: string, producer: string, modelVersion?: string, evidenceRefs?: string[], confidence?: number): Promise<ClaimEntry> {
    try { return await postToBackend('add_claim', { statement, classification, producer, model_version: modelVersion, evidence_refs: evidenceRefs, confidence }); } catch { /* fallback */ }
    return { claim_id: 'new-' + Math.random().toString(36).slice(2), statement, classification, producer, model_version: modelVersion, evidence_refs: evidenceRefs || [], confidence: confidence || 1.0, confidence_label: 'high', validation_status: 'Under Review', created_at: new Date().toISOString() };
  },

  async updateClaimStatus(claimId: string, status: string): Promise<any> {
    try { return await postToBackend('update_claim_status', { claim_id: claimId, status }); } catch { /* fallback */ }
    return { status: 'ok' };
  },

  // ── Comms — Messages ──────────────────────────────────────────────
  async sendMessage(type: string, subject: string, body: string, toIds: number[], priority: string = 'NORMAL', parentMessageId?: string, ccIds?: number[]): Promise<Message> {
    try { return await postToBackend('send_message', { type, subject, body, to_ids: toIds, priority, parent_message_id: parentMessageId, cc_ids: ccIds, unit_id: 1, unit_name: 'Station' }); } catch { /* fallback */ }
    return { message_id: 'm-' + Math.random().toString(36).slice(2), type, sender: { employee_id: 1, rank: 'IO', unit: { unit_id: 1, unit_name: 'Station' } }, recipients: toIds.map(eid => ({ employee_id: eid, status: 'sent', delivered_at: new Date().toISOString() })), cc: (ccIds || []).map(eid => ({ employee_id: eid, status: 'sent' })), subject, body, linked_resources: [], attachments: [], priority, status: 'SENT', created_at: new Date().toISOString(), sent_at: new Date().toISOString(), parent_message_id: parentMessageId, thread_id: parentMessageId || undefined };
  },

  async listInbox(employeeId: number, unreadOnly: boolean = false, priorityFilter?: string, since?: string): Promise<Message[]> {
    try { return await postToBackend('list_inbox', { employee_id: employeeId, unread_only: unreadOnly, priority_filter: priorityFilter, since }); } catch { /* fallback */ }
    return [
      { message_id: 'm1', type: 'CASE_ASSIGNMENT', sender: { employee_id: 2, rank: 'SHO', unit: { unit_id: 1, unit_name: 'South Station' } }, recipients: [{ employee_id: 1, status: 'sent' }], cc: [], subject: 'Investigate Case 104...001', body: 'Case assigned for robbery investigation. Details in linked case.', linked_resources: [{ resourceType: 'CASE', resourceId: 10001 }], attachments: [], priority: 'HIGH', status: 'SENT', created_at: new Date().toISOString(), sent_at: new Date().toISOString() },
      { message_id: 'm2', type: 'STATUS_UPDATE', sender: { employee_id: 3, rank: 'IO', unit: { unit_id: 2, unit_name: 'East Station' } }, recipients: [{ employee_id: 1, status: 'read', read_at: new Date().toISOString() }], cc: [], subject: 'Arrest update — Case 104...002', body: 'Suspect arrested at KG Halli. Further investigation underway.', linked_resources: [], attachments: [], priority: 'NORMAL', status: 'READ', created_at: new Date(Date.now() - 86400000).toISOString(), sent_at: new Date(Date.now() - 86400000).toISOString() },
      { message_id: 'm3', type: 'APPROVAL_REQUEST', sender: { employee_id: 4, rank: 'IO', unit: { unit_id: 1, unit_name: 'South Station' } }, recipients: [{ employee_id: 1, status: 'read' }], cc: [], subject: 'Chargesheet review — Case 104...003', body: 'Chargesheet ready for your review. 4 evidence items attached.', linked_resources: [{ resourceType: 'CHARGESHEET', resourceId: 5678 }], attachments: [{ file_id: 'f1', file_name: 'chargesheet_draft.pdf', mime_type: 'application/pdf', size_bytes: 245000 }], priority: 'HIGH', status: 'READ', created_at: new Date(Date.now() - 172800000).toISOString(), sent_at: new Date(Date.now() - 172800000).toISOString() },
    ];
  },

  async getMessage(messageId: string): Promise<Message> {
    try { return await postToBackend('get_message', { message_id: messageId }); } catch { /* fallback */ }
    return { message_id: messageId, type: 'STATUS_UPDATE', sender: { employee_id: 1, rank: 'IO', unit: { unit_id: 1, unit_name: 'Station' } }, recipients: [], cc: [], subject: 'Message', body: 'Details...', linked_resources: [], attachments: [], priority: 'NORMAL', status: 'SENT', created_at: new Date().toISOString() };
  },

  async markRead(messageId: string, employeeId: number): Promise<boolean> {
    try { const r = await postToBackend('mark_read', { message_id: messageId, employee_id: employeeId }); return r.ok; } catch { return true; }
  },

  async acknowledgeMessage(messageId: string, employeeId: number): Promise<boolean> {
    try { const r = await postToBackend('acknowledge_message', { message_id: messageId, employee_id: employeeId }); return r.ok; } catch { return true; }
  },

  async getThread(messageId: string): Promise<Message[]> {
    try { return await postToBackend('get_thread', { message_id: messageId }); } catch { return []; }
  },

  // ── Comms — Permissions ───────────────────────────────────────────
  async checkPermission(rank: string, resourceType: string, action: string, scope?: string): Promise<PermissionCheck> {
    try { return await postToBackend('check_permission', { rank, resource_type: resourceType, action, scope }); } catch { /* fallback */ }
    const denied = action === 'APPROVE' && rank === 'Sub-Inspector';
    return { resource_type: resourceType, action, allowed: !denied, denial_reason: denied ? `${rank} cannot ${action} ${resourceType}` : '' };
  },

  async delegatePermission(grantorId: number, granteeId: number, permission: string, scope: string = 'own_station', validUntil?: string, reason?: string): Promise<TempPermission> {
    try { return await postToBackend('delegate_permission', { grantor_id: grantorId, grantee_id: granteeId, permission, scope, valid_until: validUntil, reason }); } catch { /* fallback */ }
    return { permission_id: 'dp-' + Math.random().toString(36).slice(2), grantor_employee_id: grantorId, grantee_employee_id: granteeId, permission, scope, valid_from: new Date().toISOString(), valid_until: validUntil || new Date(Date.now() + 604800000).toISOString(), reason: reason || '', status: 'active' };
  },

  async revokeDelegation(permissionId: string): Promise<boolean> {
    try { const r = await postToBackend('revoke_delegation', { permission_id: permissionId }); return r.ok; } catch { return true; }
  },

  async listDelegations(grantorId?: number, granteeId?: number): Promise<TempPermission[]> {
    try { return await postToBackend('list_delegations', { grantor_id: grantorId, grantee_id: granteeId }); } catch { return []; }
  },

  async setEmergency(active: boolean, durationHours: number = 72): Promise<boolean> {
    try { const r = await postToBackend('set_emergency', { active, duration_hours: durationHours }); return r.emergency; } catch { return active; }
  },

  async getEmergencyStatus(): Promise<boolean> {
    try { const r = await postToBackend('get_emergency_status'); return r.emergency; } catch { return false; }
  },

  // ── Comms — Groups ────────────────────────────────────────────────
  async createDynamicGroup(name: string, groupType: string, leadId: number, caseIds?: number[], dissolveHours?: number, description?: string, offenderIds?: number[]): Promise<DynamicGroup> {
    try { return await postToBackend('create_dynamic_group', { name, group_type: groupType, lead_id: leadId, case_ids: caseIds, dissolve_hours: dissolveHours, description, offender_ids: offenderIds }); } catch { /* fallback */ }
    return { group_id: 'g-' + Math.random().toString(36).slice(2), group_name: name, group_type: groupType, description, lead_employee_id: leadId, linked_case_ids: caseIds || [], linked_offender_ids: offenderIds || [], dissolve_at: dissolveHours ? new Date(Date.now() + dissolveHours * 3600000).toISOString() : undefined, status: 'active', created_at: new Date().toISOString() };
  },

  async listDynamicGroups(activeOnly: boolean = true): Promise<DynamicGroup[]> {
    try { return await postToBackend('list_dynamic_groups', { active_only: activeOnly }); } catch { return []; }
  },

  async dissolveGroup(groupId: string): Promise<boolean> {
    try { const r = await postToBackend('dissolve_group', { group_id: groupId }); return r.ok; } catch { return true; }
  },

  async addGroupMember(groupId: string, employeeId: number, roleInGroup: string = 'member'): Promise<GroupMember> {
    try { return await postToBackend('add_group_member', { group_id: groupId, employee_id: employeeId, role_in_group: roleInGroup }); } catch { /* fallback */ }
    return { employee_id: employeeId, role_in_group: roleInGroup, joined_at: new Date().toISOString() };
  },

  async removeGroupMember(groupId: string, employeeId: number): Promise<boolean> {
    try { const r = await postToBackend('remove_group_member', { group_id: groupId, employee_id: employeeId }); return r.ok; } catch { return true; }
  },

  async listGroupMembers(groupId: string): Promise<GroupMember[]> {
    try { return await postToBackend('list_group_members', { group_id: groupId }); } catch { return []; }
  },

  async listMyGroups(employeeId: number): Promise<DynamicGroup[]> {
    try { return await postToBackend('list_my_groups', { employee_id: employeeId }); } catch { return []; }
  },

  // ── Comms — Coordination ──────────────────────────────────────────
  async createCoordination(requestType: string, targetUnitId: number, priority: string, description: string, linkedCaseIds?: number[]): Promise<CoordinationRequest> {
    const userCtx = JSON.parse(localStorage.getItem('user_context') || '{}');
    const fromId = Number(userCtx?.user_id?.replace(/\D/g, '') || 1);
    try { return await postToBackend('create_coordination', { from_id: fromId, request_type: requestType, target_unit_id: targetUnitId, priority, description, linked_case_ids: linkedCaseIds || [] }); } catch { /* fallback */ }
    return { request_id: 'cr-' + Math.random().toString(36).slice(2), request_type: requestType, from_employee_id: fromId, target_unit_id: targetUnitId, priority, description, linked_case_ids: linkedCaseIds || [], status: 'pending', created_at: new Date().toISOString(), responding_unit_id: undefined, responded_at: undefined };
  },

  async updateCoordination(requestId: string, status: string, assignedTo?: number): Promise<boolean> {
    try { const r = await postToBackend('update_coordination', { request_id: requestId, status, assigned_to: assignedTo }); return r.ok; } catch { return true; }
  },

  async listCoordination(fromId?: number, toUnit?: number, status?: string): Promise<CoordinationRequest[]> {
    try { return await postToBackend('list_coordination', { from_id: fromId, to_unit: toUnit, status }); } catch { return []; }
  },

  async listAuditLog(limit?: number, eventType?: string, category?: string, actor?: string): Promise<AuditLogEntry[]> {
    try { return await postToBackend('list_audit_log', { limit, event_type: eventType, category, actor }); } catch { return []; }
  },

  async login(kgid: string, password: string): Promise<LoginResponse> {
    try {
      const res = await postToBackend('login', { kgid, password });
      if (res && res.token) {
        localStorage.setItem('token', res.token);
        localStorage.setItem('user_context', JSON.stringify(res.user));
        return res;
      }
    } catch (e) {
      console.warn("Failed live login, using mock database.", e);
    }

    await delay(500);
    if (users[kgid]) {
      localStorage.setItem('token', users[kgid].token);
      localStorage.setItem('user_context', JSON.stringify(users[kgid].user));
      return users[kgid];
    }
    throw new Error('Invalid credentials');
  },

  async chatQuery(message: string, conversationId?: string): Promise<ChatMessage> {
    try {
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
    } catch (e) {
      console.warn("Failed live chatQuery, using fallback mock.", e);
    }

    await delay(800);
    const lowercase = message.toLowerCase();

    let response: { text: string; kn: string; sql?: string; chart?: string; followups: string[]; evidence?: { label: string; count: number; table: string }[]; warnings?: string[] };

    if (lowercase.includes('theft') || lowercase.includes('steal')) {
      response = {
        text: 'Found 2,847 theft cases in Bangalore for the current year. This represents a 12.4% increase compared to the same period last year. The areas most affected are Whitefield (312 cases), Koramangala (289 cases), and Indiranagar (245 cases).',
        kn: 'ಪ್ರಸಕ್ತ ವರ್ಷದಲ್ಲಿ ಬೆಂಗಳೂರಿನಲ್ಲಿ 2,847 ಕಳ್ಳತನ ಪ್ರಕರಣಗಳು ಪತ್ತೆಯಾಗಿವೆ. ಹಿಂದಿನ ವರ್ಷಕ್ಕೆ ಹೋಲಿಸಿದರೆ ಇದು ಶೇಕಡ 12.4 ರಷ್ಟು ಹೆಚ್ಚಳವಾಗಿದೆ.',
        sql: "SELECT CrimeMinorHeadID, COUNT(ROWID) AS cnt FROM CaseMaster WHERE CrimeMinorHeadID IN (SELECT CrimeSubHeadID FROM CrimeSubHead WHERE CrimeHeadName = 'Theft')",
        chart: 'bar_chart',
        followups: ['Which police station has the most?', 'Show on map', 'Compare with last year'],
        evidence: [{ label: 'CaseMaster records', count: 2847, table: 'CaseMaster' }],
        warnings: ['Note: mock data — not from live database'],
      };
    } else if (lowercase.includes('murder') || lowercase.includes('homicide') || lowercase.includes('death')) {
      response = {
        text: '42 murder cases have been registered in Bangalore Urban district this year. Of these, 28 (66.7%) have been solved. The clearance rate is above the national average of 62%.',
        kn: 'ಈ ವರ್ಷ ಬೆಂಗಳೂರು ನಗರ ಜಿಲ್ಲೆಯಲ್ಲಿ 42 ನರಹತ್ಯೆ ಪ್ರಕರಣಗಳು ದಾಖಲಾಗಿವೆ. ಇವುಗಳಲ್ಲಿ 28 (66.7%) ಪ್ರಕರಣಗಳನ್ನು ಭೇದಿಸಲಾಗಿದೆ.',
        chart: 'trend_chart',
        followups: ['Show by month', 'Compare with last year', 'Which weapon type is common?'],
        evidence: [{ label: 'CaseMaster records', count: 42, table: 'CaseMaster' }],
        warnings: ['Note: mock data — not from live database'],
      };
    } else if (lowercase.includes('traffic')) {
      response = {
        text: 'Traffic violations in Bangalore have increased by 8.3% this year. A total of 45,231 challans were issued. The highest number of violations are for signal jumping (12,847) and wrong-side driving (8,234).',
        kn: 'ಬೆಂಗಳೂರಿನಲ್ಲಿ ಸಂಚಾರ ಉಲ್ಲಂಘನೆಗಳು ಶೇಕಡ 8.3 ರಷ್ಟು ಹೆಚ್ಚಾಗಿವೆ. ಒಟ್ಟು 45,231 ಚಾಲನ್‌ಗಳನ್ನು ನೀಡಲಾಗಿದೆ.',
        followups: ['Show top 5 violation spots', 'Monthly trend', 'Revenue collected'],
        evidence: [{ label: 'TrafficViolation records', count: 45231, table: 'TrafficViolation' }],
        warnings: ['Note: mock data — TrafficViolation table may not exist'],
      };
    } else if (lowercase.includes('cyber')) {
      response = {
        text: '2,134 cyber crime cases were reported in Karnataka this year. The most common types are phishing (834), online fraud (612), and identity theft (388). Bengaluru Urban accounts for 58% of all cases.',
        kn: 'ಈ ವರ್ಷ ಕರ್ನಾಟಕದಲ್ಲಿ 2,134 ಸೈಬರ್ ಅಪರಾಧ ಪ್ರಕರಣಗಳು ವರದಿಯಾವೆ. ಸಾಮಾನ್ಯ ವಿಧಗಳೆಂದರೆ ಫಿಶಿಂಗ್ (834), ಆನ್‌ಲೈನ್ ವಂಚನೆ (612) ಮತ್ತು ಗುರುತಿನ ಕಳ್ಳತನ (388).',
        chart: 'pie_chart',
        followups: ['Show by district', 'Top cyber crime hotspots', 'Recovery rate'],
        evidence: [{ label: 'CyberCrime records', count: 2134, table: 'CyberCrime' }],
        warnings: ['Note: mock data — CyberCrime table may not exist'],
      };
    } else if (lowercase.includes('history') || lowercase.includes('cases') || lowercase.includes('status')) {
      response = {
        text: 'There are 156 active cases currently under investigation. Case clearance rate is 71.2%. Average investigation time is 45 days for non-cognizable and 72 days for cognizable offenses.',
        kn: 'ಪ್ರಸ್ತುತ 156 ಸಕ್ರಿಯ ಪ್ರಕರಣಗಳು ತನಿಖೆಯಲ್ಲಿವೆ. ಪ್ರಕರಣ ಭೇದನ ದರ ಶೇಕಡ 71.2 ರಷ್ಟಿದೆ.',
        followups: ['Show pending cases', 'Show by officer', 'Overdue cases'],
        evidence: [{ label: 'CaseMaster records', count: 156, table: 'CaseMaster' }],
        warnings: ['Note: mock data — not from live database'],
      };
    } else if (lowercase.includes('forecast') || lowercase.includes('predict') || lowercase.includes('future')) {
      response = {
        text: 'Based on Prophet time-series forecasting, theft cases in Bangalore are projected to reach 3,200-3,500 in the next quarter — a 12-18% increase. Crime rates are expected to peak during October-December (festive season).',
        kn: 'ಪ್ರವಾದಿ ಸಮಯ-ಸರಣಿ ಮುನ್ಸೂಚನೆಯ ಆಧಾರದ ಮೇಲೆ, ಮುಂದಿನ ತ್ರೈಮಾಸಿಕದಲ್ಲಿ ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳ್ಳತನ ಪ್ರಕರಣಗಳು 3,200-3,500 ತಲುಪುವ ನಿರೀಕ್ಷೆಯಿದೆ.',
        chart: 'forecast_chart',
        followups: ['Show by district', 'What is driving the increase?', 'Confidence intervals'],
        evidence: [{ label: 'Forecast model output', count: 1, table: 'ForecastResult' }],
        warnings: ['Note: mock data — not from live database'],
      };
    } else if (lowercase.includes('hotspot') || lowercase.includes('area') || lowercase.includes('location')) {
      response = {
        text: 'DBSCAN analysis identified 8 high-crime hotspots in Bangalore. The highest density cluster is in KG Halli (23 theft cases, 0.8km radius). Other hotspots include Shivajinagar, City Market, and Majestic area.',
        kn: 'ಡಿಬಿಎಸ್ಸಿಎಎನ್ ವಿಶ್ಲೇಷಣೆಯು ಬೆಂಗಳೂರಿನಲ್ಲಿ 8 ಹೆಚ್ಚಿನ ಅಪರಾಧ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳನ್ನು ಗುರುತಿಸಿದೆ.',
        chart: 'map_view',
        followups: ['Show on map', 'Patrol recommendations', 'Time-based analysis'],
        evidence: [{ label: 'DBSCAN clusters', count: 8, table: 'HotspotCluster' }],
        warnings: ['Note: mock data — not from live database'],
      };
    } else {
      response = {
        text: 'Here is a summary of current crime statistics across Karnataka:',
        kn: 'ಕರ್ನಾಟಕದಾದ್ಯಂತದ ಪ್ರಸ್ತುತ ಅಪರಾಧ ಅಂಕಿಅಂಶಗಳ ಸಾರಾಂಶ ಇಲ್ಲಿದೆ:',
        followups: ['Show theft cases in Bangalore', 'Show murder statistics', 'What about cyber crime?', 'Show hotspot areas', 'Predict future trends'],
        evidence: [{ label: 'Aggregated statistics', count: 1, table: 'Multiple sources' }],
        warnings: ['Note: mock data — not from live database'],
      };
    }

    return {
      message_id: Math.random().toString(36).slice(2),
      message_type: 'ai_response',
      content_text: response.text,
      content_kannada: response.kn,
      sql_text: response.sql,
      chart_recommendation: response.chart,
      evidence_refs: response.evidence ? response.evidence.map(e => ({
        evidence_id: `ev_${Math.random().toString(36).slice(2, 8)}`,
        evidence_type: 'database_fact',
        source_table: e.table,
        source_record_count: e.count,
        display_label: `${e.count.toLocaleString()} records from ${e.table}`,
      })) : [],
      data_quality_warnings: response.warnings || [],
      tool_params: {},
      suggested_followups: response.followups,
      created_at: new Date().toISOString(),
    };
  },

  async getForecastData(category?: string, district?: string): Promise<ForecastDataPoint[]> {
    try {
      return await postToBackend('get_forecast', { category, district });
    } catch (e) {
      console.warn("Failed live getForecastData, using fallback mock.", e);
    }

    await delay(400);
    const cat = category || 'Theft';
    const dist = district || 'Bengaluru Urban';
    const seed = cat.length + dist.length;
    const data: ForecastDataPoint[] = [];
    for (let i = 1; i <= 30; i++) {
      const base = 20 + seededRandom(seed + i) * 30;
      const noise = (seededRandom(seed + i + 100) - 0.5) * 10;
      data.push({
        date: `Day ${i}`,
        predicted: Math.round((base + noise) * 10) / 10,
        upper: Math.round((base + noise + 8 + seededRandom(seed + i + 200) * 6) * 10) / 10,
        lower: Math.round((base + noise - 8 - seededRandom(seed + i + 300) * 6) * 10) / 10,
        actual: i <= 7 ? Math.round((base + seededRandom(seed + i + 400) * 20) * 10) / 10 : undefined,
        category: cat,
        district: dist,
      });
    }
    return data;
  },

  async getMultiForecast(): Promise<{ category: string; data: ForecastDataPoint[] }[]> {
    try {
      return await postToBackend('get_multi_forecast');
    } catch (e) {
      console.warn("Failed live getMultiForecast, using fallback mock.", e);
    }

    await delay(500);
    const categories = ['Theft', 'Robbery', 'Assault', 'Cyber Crime', 'Burglary'];
    const results = await Promise.all(
      categories.map(cat => this.getForecastData(cat, 'Bengaluru Urban').then(data => ({ category: cat, data })))
    );
    return results;
  },

  async getDistrictForecasts(): Promise<{ district: string; data: ForecastDataPoint[] }[]> {
    try {
      return await postToBackend('get_district_forecasts');
    } catch (e) {
      console.warn("Failed live getDistrictForecasts, using fallback mock.", e);
    }

    await delay(500);
    const topDistricts = ['Bengaluru Urban', 'Mysuru', 'Hubballi-Dharwad', 'Mangaluru', 'Belagavi'];
    const results = await Promise.all(
      topDistricts.map(dist => this.getForecastData('Theft', dist).then(data => ({ district: dist, data })))
    );
    return results;
  },

  async getOffenderProfile(name: string): Promise<OffenderProfile> {
    try {
      return await postToBackend('get_offender_profile', { name });
    } catch (e) {
      console.warn("Failed live getOffenderProfile, using fallback mock.", e);
    }

    await delay(600);
    const score = this.getPriorityScore();
    return {
      entity_name: name,
      total_score: score.total_score,
      risk_tier: score.risk_tier,
      features: score.features,
      linked_cases: [
        { case_id: 101, crime_no: 'CN202400101', crime_type: 'Theft', year: 2024, status: 'Under Investigation' },
        { case_id: 201, crime_no: 'CN202400201', crime_type: 'Robbery', year: 2023, status: 'Charge Sheeted' },
        { case_id: 301, crime_no: 'CN202400301', crime_type: 'Assault', year: 2024, status: 'Under Investigation' },
        { case_id: 401, crime_no: 'CN202300401', crime_type: 'Burglary', year: 2023, status: 'Closed' },
        { case_id: 501, crime_no: 'CN202400501', crime_type: 'Cheating', year: 2024, status: 'Pending' },
        { case_id: 601, crime_no: 'CN202400601', crime_type: 'Kidnapping', year: 2024, status: 'Under Investigation' },
        { case_id: 701, crime_no: 'CN202300701', crime_type: 'Theft', year: 2023, status: 'Charge Sheeted' },
        { case_id: 801, crime_no: 'CN202400801', crime_type: 'Robbery', year: 2024, status: 'Under Investigation' },
      ],
      disclaimer: 'This score is an analytical tool for investigation prioritization. It does not indicate guilt, dangerousness, or likelihood of future crime.',
    };
  },

  async createOffenderProfile(profile: { accused_name: string; case_master_id: number; age_year: number; gender_id: number; person_id: string }): Promise<any> {
    try {
      return await postToBackend('create_offender_profile', profile);
    } catch (e) {
      console.warn("Failed live createOffenderProfile, executing mock completion.", e);
    }
    await delay(600);
    return { status: "success", message: "Accused profile created successfully." };
  },


  getPriorityScore(): PriorityScore {
    return {
      total_score: 56.45,
      risk_tier: 'ELEVATED',
      score_version: '1.0.0',
      features: [
        { name: 'Case Frequency', raw_value: '12 cases / 3 years', normalized_value: 0.54, weight: 0.25, contribution: 13.5 },
        { name: 'Crime Type Diversity', raw_value: '4 types', normalized_value: 0.40, weight: 0.15, contribution: 6.0 },
        { name: 'Geographic Spread', raw_value: '3 districts', normalized_value: 0.60, weight: 0.15, contribution: 9.0 },
        { name: 'Recent Activity', raw_value: '3 cases in 90 days', normalized_value: 0.60, weight: 0.20, contribution: 12.0 },
        { name: 'Co-Accused Network', raw_value: '8 co-accused', normalized_value: 0.53, weight: 0.15, contribution: 8.0 },
        { name: 'Arrest Ratio', raw_value: '80% arrest rate', normalized_value: 0.80, weight: 0.10, contribution: 8.0 },
      ],
      disclaimer: 'This score is an analytical tool for investigation prioritization.',
    };
  },

  async getTrends(): Promise<TrendDataPoint[]> {
    try {
      return await postToBackend('get_trends');
    } catch (e) {
      console.warn("Failed live getTrends, using fallback mock.", e);
    }

    await delay(400);
    const types = ['Theft', 'Robbery', 'Assault', 'Burglary', 'Cyber Crime'];
    return types.flatMap(type => [
      { period: '2024-01', count: Math.floor(180 + seededRandom(type.length + 1) * 200), pct_change: undefined, crime_type: type },
      { period: '2024-02', count: Math.floor(180 + seededRandom(type.length + 2) * 200), pct_change: 9.4, crime_type: type },
      { period: '2024-03', count: Math.floor(180 + seededRandom(type.length + 3) * 200), pct_change: 12.9, crime_type: type },
      { period: '2024-04', count: Math.floor(180 + seededRandom(type.length + 4) * 200), pct_change: 8.0, crime_type: type },
      { period: '2024-05', count: Math.floor(180 + seededRandom(type.length + 5) * 200), pct_change: -4.5, crime_type: type },
      { period: '2024-06', count: Math.floor(180 + seededRandom(type.length + 6) * 200), pct_change: 15.8, crime_type: type },
    ]);
  },

  async getHotspots(): Promise<HotspotCluster[]> {
    try {
      return await postToBackend('get_hotspots');
    } catch (e) {
      console.warn("Failed live getHotspots, using fallback mock.", e);
    }

    await delay(400);
    return [
      { cluster_id: 1, centroid_lat: 12.9716, centroid_lng: 77.5946, case_count: 12, radius_km: 0.8, crime_type: 'Theft' },
      { cluster_id: 2, centroid_lat: 12.9344, centroid_lng: 77.6102, case_count: 8, radius_km: 0.5, crime_type: 'Robbery' },
      { cluster_id: 3, centroid_lat: 12.9612, centroid_lng: 77.5643, case_count: 15, radius_km: 1.2, crime_type: 'Assault' },
      { cluster_id: 4, centroid_lat: 12.9210, centroid_lng: 77.5910, case_count: 6, radius_km: 0.4, crime_type: 'Burglary' },
      { cluster_id: 5, centroid_lat: 12.9850, centroid_lng: 77.6100, case_count: 20, radius_km: 1.0, crime_type: 'Cyber Crime' },
      { cluster_id: 6, centroid_lat: 12.9500, centroid_lng: 77.5700, case_count: 10, radius_km: 0.6, crime_type: 'Cheating' },
      { cluster_id: 7, centroid_lat: 12.9400, centroid_lng: 77.6200, case_count: 7, radius_km: 0.3, crime_type: 'Kidnapping' },
      { cluster_id: 8, centroid_lat: 12.9800, centroid_lng: 77.5800, case_count: 18, radius_km: 0.9, crime_type: 'Theft' },
    ];
  },

  async getNetwork(accusedName: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
    try {
      return await postToBackend('get_network', { accused_name: accusedName });
    } catch (e) {
      console.warn("Failed live getNetwork, using fallback mock.", e);
    }

    await delay(600);
    const tiers = ['LOW', 'MODERATE', 'ELEVATED', 'HIGH'] as const;
    const nodes: GraphNode[] = accusedNames.slice(0, 8).map((n, i) => ({
      id: `node_${i}`,
      label: n,
      node_type: 'accused',
      cases: Math.floor(seededRandom(i + 100) * 8) + 1,
      risk_tier: tiers[i % 4],
    }));
    const edges: GraphEdge[] = [];
    for (let i = 0; i < 14; i++) {
      const s = Math.floor(seededRandom(i + 200) * nodes.length);
      let t = Math.floor(seededRandom(i + 300) * nodes.length);
      if (s === t) t = (t + 1) % nodes.length;
      edges.push({
        id: `edge_${i}`,
        source: nodes[s].id,
        target: nodes[t].id,
        weight: Math.floor(seededRandom(i + 400) * 4) + 1,
        shared_cases: [101 + i, 102 + i],
      });
    }
    return { nodes, edges };
  },

  async getDashboardKpis(): Promise<{ label: string; value: string; change: string; icon: string }[]> {
    try {
      return await postToBackend('get_dashboard_kpis');
    } catch (e) {
      console.warn("Failed live getDashboardKpis, using fallback mock.", e);
    }

    return [
      { label: 'Total FIRs', value: '12,847', change: '+12.4%', icon: 'FileText' },
      { label: 'Active Cases', value: '156', change: '-8.2%', icon: 'Activity' },
      { label: 'Clearance Rate', value: '71.2%', change: '+3.1%', icon: 'CheckCircle' },
      { label: 'Hotspots Active', value: '8', change: '+2', icon: 'MapPin' },
    ];
  },

  async getAlerts(): Promise<{ id: string; severity: string; title: string; description: string; rule_id: string; trigger_condition: string; created_at: string; acknowledged: boolean }[]> {
    try {
      return await postToBackend('get_alerts');
    } catch (e) {
      console.warn("Failed live getAlerts, using fallback mock.", e);
    }

    return [
      { id: 'a1', severity: 'critical', title: 'Theft Surge Detected', description: 'Theft cases in Whitefield up 34% this month — automated threshold breach.', rule_id: 'R-THEFT-001', trigger_condition: 'pct_change > 25%', created_at: new Date().toISOString(), acknowledged: false },
      { id: 'a2', severity: 'warning', title: 'Seasonal Pattern Trigger', description: 'Burglary cases expected to rise 18-22% during upcoming festive season.', rule_id: 'R-SEASONAL-003', trigger_condition: 'Prophet forecast 80% CI breach', created_at: new Date(Date.now() - 86400000).toISOString(), acknowledged: false },
      { id: 'a3', severity: 'info', title: 'New Crime Type Detected', description: 'Cryptocurrency fraud cases emerging in Bengaluru Urban — 7 cases this week.', rule_id: 'R-NEWTYPE-007', trigger_condition: 'new_crime_type frequency > 5/week', created_at: new Date(Date.now() - 172800000).toISOString(), acknowledged: true },
      { id: 'a4', severity: 'warning', title: 'Hotspot Expansion', description: 'KG Halli hotspot radius expanded from 0.8km to 1.2km — increased patrol recommended.', rule_id: 'R-HOTSPOT-002', trigger_condition: 'DBSCAN cluster radius change > 30%', created_at: new Date(Date.now() - 259200000).toISOString(), acknowledged: false },
      { id: 'a5', severity: 'critical', title: 'Recidivism Alert', description: 'Known offender Ravi Kumar linked to 3 new cases this month — Priority Score now ELEVATED.', rule_id: 'R-RECIDIVISM-004', trigger_condition: 'Priority Score increase > 15 points in 30 days', created_at: new Date(Date.now() - 3600000).toISOString(), acknowledged: false },
    ];
  },

  async commanderQuery(query: string): Promise<{ mission_id: string; intents: any; tasks: any[]; summary: string; status: string }> {
    try {
      return await postToBackend('commander_query', { query });
    } catch (e) {
      console.warn("Failed live commanderQuery, using fallback mock.", e);
    }
    await delay(600);
    return {
      mission_id: 'mock-mission-1',
      intents: { primary_intent: 'database_query', secondary_intents: ['trend_analysis'], confidence: 0.85 },
      tasks: [
        { task_id: 't1', agent: 'database_query', query, status: 'completed', result: 'Found 2,847 theft cases.', evidence: [{ evidence_id: 'e1', evidence_type: 'database_fact', source_table: 'CrimeIncident' }] },
        { task_id: 't2', agent: 'trend_analysis', query, status: 'completed', result: 'Theft cases up 12.4% YoY.', evidence: [{ evidence_id: 'e2', evidence_type: 'computed_statistic', source_table: 'CrimeIncident' }] },
      ],
      summary: 'Mission complete: 2/2 tasks succeeded, 0 failed.',
      status: 'completed',
    };
  },

  async getActivityFeed(): Promise<{ id: string; text: string; time: string; type: string }[]> {
    try {
      return await postToBackend('get_activity_feed');
    } catch (e) {
      console.warn("Failed live getActivityFeed, using fallback mock.", e);
    }

    return [
      { id: 'f1', text: 'New FIR filed: Theft at Whitefield station', time: '2 min ago', type: 'case' },
      { id: 'f2', text: 'Offender score updated for Suresh P — MODERATE', time: '15 min ago', type: 'score' },
      { id: 'f3', text: 'Community detection run on Bengaluru network — 4 communities found', time: '1 hour ago', type: 'network' },
      { id: 'f4', text: 'Prophet forecast refreshed — next 30 days projected', time: '2 hours ago', type: 'forecast' },
      { id: 'f5', text: 'Alert acknowledged: Theft surge in Whitefield', time: '3 hours ago', type: 'alert' },
    ];
  },
};
