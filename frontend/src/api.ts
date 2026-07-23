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
  sendMessage: (message: string, conversation_id?: number, language?: string) =>
    j("/chat/message", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id, language }),
    }),

  // analytics
  overview: () => j("/analytics/overview"),
  byType: () => j("/analytics/by-type"),
  byHead: () => j("/analytics/by-head"),
  trend: (crimeType?: string) =>
    j(`/analytics/trend${crimeType ? `?crime_type=${encodeURIComponent(crimeType)}` : ""}`),
  hotspots: (crimeType?: string) =>
    j(`/analytics/hotspots${crimeType ? `?crime_type=${encodeURIComponent(crimeType)}` : ""}`),
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

  // audit / governance
  auditLogs: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as any
    ).toString();
    return j(`/audit/logs${qs ? `?${qs}` : ""}`);
  },
  auditSummary: () => j("/audit/summary"),
};
