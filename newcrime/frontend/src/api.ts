const BASE = "/api";

// Attach the signed-in officer's identity so the backend can enforce RBAC,
// mask PII and write the audit trail. (Local prototype — a production build
// would use a verified session token instead of headers.)
function authHeaders(): Record<string, string> {
  try {
    const u = JSON.parse(localStorage.getItem("ci-user") || "null");
    if (!u) return {};
    return {
      "X-User-Id": String(u.id ?? ""),
      "X-User-Name": u.full_name ?? "",
      "X-User-Role": u.role ?? "",
      "X-User-District": u.district ?? "",
      "X-User-Subdivision": u.subdivision ?? "",
      "X-User-Range": u.range_name ?? "",
    };
  } catch {
    return {};
  }
}

async function j<T = any>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(opts?.headers || {}) },
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${msg}`);
  }
  return res.json();
}

export const api = {
  health: () => j("/health"),

  // auth
  login: (username: string, password: string) =>
    j("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
  demoUsers: () => j("/auth/users"),

  // chat
  conversations: () => j("/chat/conversations"),
  conversation: (id: number) => j(`/chat/conversations/${id}`),
  deleteConversation: (id: number) =>
    j(`/chat/conversations/${id}`, { method: "DELETE" }),
  sendMessage: (message: string, conversation_id?: number, language?: string, files?: File[]) => {
    if (files && files.length > 0) {
      const fd = new FormData();
      fd.append("message", message);
      if (conversation_id) fd.append("conversation_id", String(conversation_id));
      if (language) fd.append("language", language);
      files.forEach((f, i) => fd.append(`file_${i}`, f));
      return fetch("/api/chat/message", { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
    }
    return j("/chat/message", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id, language }),
    });
  },

  // analytics
  overview: () => j("/analytics/overview"),
  byType: () => j("/analytics/by-type"),
  byHead: () => j("/analytics/by-head"),
  trend: (crimeType?: string) =>
    j(`/analytics/trend${crimeType ? `?crime_type=${encodeURIComponent(crimeType)}` : ""}`),
  hotspots: (crimeType?: string) =>
    j(`/analytics/hotspots${crimeType ? `?crime_type=${encodeURIComponent(crimeType)}` : ""}`),
  hotspotDashboard: (params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v)).toString();
    return j(`/analytics/hotspot-dashboard${qs ? `?${qs}` : ""}`);
  },
  crimeCategory: (crimeType: string) => j(`/analytics/crime-category/${encodeURIComponent(crimeType)}`),
  geo: (crimeType?: string) =>
    j(`/analytics/geo${crimeType ? `?crime_type=${encodeURIComponent(crimeType)}` : ""}`),
  temporal: () => j("/analytics/temporal"),
  patterns: () => j("/analytics/patterns"),

  // cases
  cases: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as any
    ).toString();
    return j(`/cases${qs ? `?${qs}` : ""}`);
  },
  caseFilters: () => j("/cases/filters"),
  caseDetail: (id: number) => j(`/cases/${id}`),
  similarCases: (id: number) => j(`/cases/${id}/similar`),
  createFIR: (data: Record<string, any>) => {
    const fd = new FormData();
    Object.entries(data).forEach(([k, v]) => { if (v !== undefined && v !== "") fd.append(k, String(v)); });
    return fetch(`${BASE}/cases`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },
  updateCase: (id: number, data: Record<string, any>) => {
    const fd = new FormData();
    Object.entries(data).forEach(([k, v]) => { if (v !== undefined && v !== "") fd.append(k, String(v)); });
    return fetch(`${BASE}/cases/${id}`, { method: "PUT", headers: authHeaders(), body: fd }).then(r => r.json());
  },
  generateChargesheet: (caseId: number) => {
    return fetch(`${BASE}/cases/${caseId}/chargesheet`, { method: "POST", headers: { ...authHeaders(), "Content-Type": "application/json" }, body: "{}" }).then(r => r.json());
  },

  // network
  networkGraph: (minDegree = 0, gang?: string) =>
    j(`/network/graph?min_degree=${minDegree}${gang ? `&gang=${encodeURIComponent(gang)}` : ""}`),
  gangs: () => j("/network/gangs"),
  egoNetwork: (id: number) => j(`/network/accused/${id}`),

  // profiling
  offenders: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as any
    ).toString();
    return j(`/profiling/offenders${qs ? `?${qs}` : ""}`);
  },
  riskDistribution: () => j("/profiling/distribution"),
  offenderDetail: (id: number) => j(`/profiling/offender/${id}`),

  // socio
  socioGender: () => j("/socio/gender"),
  socioAge: () => j("/socio/age-bands"),
  socioSes: () => j("/socio/socio-economic"),
  socioEdu: () => j("/socio/education"),
  socioUrbanRural: () => j("/socio/urban-rural"),
  riskFactors: () => j("/socio/risk-factors"),
  crimeByDemographic: () => j("/socio/crime-by-demographic"),

  // victim analysis
  victimOverview: () => j("/victims/overview"),
  victimCrimeTypes: () => j("/victims/crime-types"),
  victimList: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as any
    ).toString();
    return j(`/victims/list${qs ? `?${qs}` : ""}`);
  },
  victimDetail: (id: number) => j(`/victims/${id}`),
  victimIntelligence: (id: number) => j(`/victims/${id}/intelligence`),
  victimRelationships: (id: number) => j(`/victims/${id}/relationships`),
  victimVulnerability: () => j("/victims/vulnerability/assessment"),
  caseVictims: (caseId: number) => j(`/investigation/${caseId}/victims`),
  addVictim: (caseId: number, v: Record<string, any>) => {
    const fd = new FormData();
    Object.entries(v).forEach(([k, val]) => fd.append(k, String(val ?? "")));
    return fetch(`/api/investigation/${caseId}/victims`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },
  updateVictim: (caseId: number, victimId: number, v: Record<string, any>) => {
    const fd = new FormData();
    Object.entries(v).forEach(([k, val]) => fd.append(k, String(val ?? "")));
    return fetch(`/api/investigation/${caseId}/victims/${victimId}`, { method: "PUT", headers: authHeaders(), body: fd }).then(r => r.json());
  },
  unlinkVictim: (caseId: number, victimId: number) =>
    fetch(`/api/investigation/${caseId}/victims/${victimId}`, { method: "DELETE", headers: authHeaders() }).then(r => r.json()),

  // approval console
  allPendingApprovals: () => j("/investigation/approvals/pending"),
  allAccessRequests: () => j("/investigation/access-requests/pending"),

  // forecasting
  predictions: (risk?: string) =>
    j(`/forecasting/predictions${risk ? `?risk_level=${risk}` : ""}`),

  // financial
  financialSummary: () => j("/financial/summary"),
  moneyGraph: (onlyFlagged = false) => j(`/financial/graph?only_flagged=${onlyFlagged}`),
  suspiciousAccounts: () => j("/financial/suspicious-accounts"),

  // alerts
  alerts: (unresolvedOnly = false) => j(`/alerts?unresolved_only=${unresolvedOnly}`),
  resolveAlert: (id: number) => j(`/alerts/${id}/resolve`, { method: "POST" }),

  // dashboards
  workspace: () => j("/workspace/overview"),
  command: () => j("/command/overview"),
  districtMap: (crimeType?: string) =>
    j(`/analytics/district-map${crimeType ? `?crime_type=${encodeURIComponent(crimeType)}` : ""}`),

  // investigation ("Work a Case")
  investigation: (caseId: number) => j(`/investigation/${caseId}`),
  setStage: (caseId: number, stage: string) => {
    const fd = new FormData(); fd.append("stage", stage);
    return fetch(`/api/investigation/${caseId}/stage`, { method: "POST", headers: authHeaders(), body: fd }).then((r) => r.json());
  },
  notes: (caseId: number) => j(`/investigation/${caseId}/notes`),
  addNote: (caseId: number, content: string) => {
    const fd = new FormData(); fd.append("content", content);
    return fetch(`/api/investigation/${caseId}/notes`, { method: "POST", headers: authHeaders(), body: fd }).then((r) => r.json());
  },
  pinNote: (noteId: number) => j(`/investigation/notes/${noteId}/pin`, { method: "POST" }),
  deleteNote: (noteId: number) => j(`/investigation/notes/${noteId}`, { method: "DELETE" }),
  witnesses: (caseId: number) => j(`/investigation/${caseId}/witnesses`),
  addWitness: (caseId: number, w: { name: string; contact?: string; statement?: string; reliability?: string }) => {
    const fd = new FormData();
    Object.entries(w).forEach(([k, v]) => fd.append(k, v ?? ""));
    return fetch(`/api/investigation/${caseId}/witnesses`, { method: "POST", headers: authHeaders(), body: fd }).then((r) => r.json());
  },
  evidence: (caseId: number) => j(`/investigation/${caseId}/evidence`),
  uploadEvidence: (caseId: number, category: string, file: File) => {
    const fd = new FormData(); fd.append("category", category); fd.append("file", file);
    return fetch(`/api/investigation/${caseId}/evidence`, { method: "POST", headers: authHeaders(), body: fd }).then((r) => r.json());
  },
  evidenceDownloadUrl: (docId: number) => `/api/investigation/evidence/${docId}/download`,
  deleteEvidence: (docId: number) => j(`/investigation/evidence/${docId}`, { method: "DELETE" }),

  // case-scoped chat
  caseChat: (caseId: number) => j(`/investigation/${caseId}/chat`),
  caseChatSend: (caseId: number, message: string, file?: File) => {
    if (file) {
      const fd = new FormData();
      fd.append("message", message);
      fd.append("file", file);
      return fetch(`/api/investigation/${caseId}/chat`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
    }
    return j(`/investigation/${caseId}/chat`, { method: "POST", body: JSON.stringify({ message }) });
  },

  // stage approvals
  requestStage: (caseId: number, stage: string, comments: string) => {
    const fd = new FormData(); fd.append("stage", stage); fd.append("comments", comments);
    return fetch(`/api/investigation/${caseId}/stage/request`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },
  caseApprovals: (caseId: number) => j(`/investigation/${caseId}/approvals`),
  reviewApproval: (approvalId: number, action: string, comments: string) => {
    const fd = new FormData(); fd.append("action", action); fd.append("comments", comments);
    return fetch(`/api/investigation/approval/${approvalId}/review`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },

  // access request
  requestAccess: (caseId: number, reason: string) => {
    const fd = new FormData(); fd.append("reason", reason);
    return fetch(`/api/investigation/${caseId}/request-access`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },
  emergencyAccess: (caseId: number, reason: string) => {
    const fd = new FormData(); fd.append("reason", reason);
    return fetch(`/api/investigation/${caseId}/emergency-access`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },
  accessRequests: (caseId: number) => j(`/investigation/${caseId}/access-requests`),
  reviewAccessRequest: (reqId: number, status: string) => {
    const fd = new FormData(); fd.append("status", status);
    return fetch(`/api/investigation/access-request/${reqId}/review`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },

  // witness with file
  addWitnessWithFile: (caseId: number, w: any, file?: File) => {
    const fd = new FormData();
    Object.entries(w).forEach(([k, v]) => fd.append(k, (v as string) ?? ""));
    if (file) fd.append("document", file);
    return fetch(`/api/investigation/${caseId}/witnesses`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },

  // evidence with remarks
  uploadEvidenceWithRemarks: (caseId: number, category: string, file: File, remarks: string) => {
    const fd = new FormData(); fd.append("category", category); fd.append("file", file); fd.append("remarks", remarks);
    return fetch(`/api/investigation/${caseId}/evidence`, { method: "POST", headers: authHeaders(), body: fd }).then(r => r.json());
  },

  // audit / governance
  auditLogs: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as any
    ).toString();
    return j(`/audit/logs${qs ? `?${qs}` : ""}`);
  },
  auditSummary: () => j("/audit/summary"),
};
