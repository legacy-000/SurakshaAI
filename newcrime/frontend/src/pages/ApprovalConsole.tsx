import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle, XCircle, Clock, Shield } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { Chip, Loading, Panel } from "../components";

export default function ApprovalConsole() {
  const { t } = useLang();
  const nav = useNavigate();
  const [stageApprovals, setStageApprovals] = useState<any[] | null>(null);
  const [accessRequests, setAccessRequests] = useState<any[] | null>(null);
  const [busy, setBusy] = useState<number | null>(null);

  const load = () => {
    api.allPendingApprovals().then(setStageApprovals).catch(() => setStageApprovals([]));
    api.allAccessRequests().then(setAccessRequests).catch(() => setAccessRequests([]));
  };
  useEffect(load, []);

  const reviewStage = async (id: number, action: string) => {
    setBusy(id);
    try { await api.reviewApproval(id, action, ""); load(); }
    finally { setBusy(null); }
  };

  const reviewAccess = async (id: number, action: string) => {
    setBusy(id);
    try { await api.reviewAccessRequest(id, action); load(); }
    finally { setBusy(null); }
  };

  if (!stageApprovals || !accessRequests) return <Loading label={t("Loading…")} />;

  return (
    <div className="grid" style={{ gap: 16, maxWidth: 900, margin: "0 auto" }}>
      {/* Summary */}
      <div className="grid cols-3">
        <Panel>
          <div className="faint" style={{ fontSize: 11, textTransform: "uppercase" }}>{t("Stage Approvals")}</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "var(--accent)" }}>{stageApprovals.length}</div>
          <div className="faint" style={{ fontSize: 11 }}>{t("pending")}</div>
        </Panel>
        <Panel>
          <div className="faint" style={{ fontSize: 11, textTransform: "uppercase" }}>{t("Access Requests")}</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "var(--amber)" }}>{accessRequests.length}</div>
          <div className="faint" style={{ fontSize: 11 }}>{t("pending")}</div>
        </Panel>
        <Panel>
          <div className="faint" style={{ fontSize: 11, textTransform: "uppercase" }}>{t("Total Pending")}</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{stageApprovals.length + accessRequests.length}</div>
        </Panel>
      </div>

      {/* Stage approval requests */}
      <Panel title={<span><Clock size={13} /> {t("Stage Advancement Requests")}</span> as any}>
        {stageApprovals.length === 0 ? (
          <div className="faint center" style={{ padding: 20 }}>{t("No pending stage approvals.")}</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {stageApprovals.map((a: any) => (
              <div key={a.id} style={{ padding: "12px 14px", border: "1px solid var(--border)",
                background: "var(--panel-2)", display: "flex", gap: 12, alignItems: "start", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontWeight: 600, cursor: "pointer", color: "var(--accent)" }}
                    onClick={() => nav(`/cases/${a.case_id}`)}>
                    {a.fir_number} — {a.case_title}
                  </div>
                  <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>
                    {t("Requested by")}: <b>{a.requested_by}</b> ({a.requested_role})
                  </div>
                  <div className="dim" style={{ fontSize: 12 }}>
                    {t("Advance to")}: <Chip kind="accent">{a.stage}</Chip>
                  </div>
                  {a.comments && <div className="faint" style={{ fontSize: 12, marginTop: 4, fontStyle: "italic" }}>{a.comments}</div>}
                  <div className="faint" style={{ fontSize: 11, marginTop: 4 }}>{new Date(a.created_at).toLocaleString()}</div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="btn primary" disabled={busy === a.id} onClick={() => reviewStage(a.id, "approved")}
                    style={{ fontSize: 12 }}>
                    <CheckCircle size={13} /> {t("Approve")}
                  </button>
                  <button className="btn ghost" disabled={busy === a.id} onClick={() => reviewStage(a.id, "rejected")}
                    style={{ fontSize: 12 }}>
                    <XCircle size={13} /> {t("Reject")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* Access requests */}
      <Panel title={<span><Shield size={13} /> {t("Access Requests")}</span> as any}>
        {accessRequests.length === 0 ? (
          <div className="faint center" style={{ padding: 20 }}>{t("No pending access requests.")}</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {accessRequests.map((r: any) => (
              <div key={r.id} style={{ padding: "12px 14px", border: "1px solid var(--border)",
                background: "var(--panel-2)", display: "flex", gap: 12, alignItems: "start", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: 200 }}>
                  <div style={{ fontWeight: 600, cursor: "pointer", color: "var(--accent)" }}
                    onClick={() => nav(`/cases/${r.case_id}`)}>
                    {r.fir_number} — {r.case_title}
                  </div>
                  <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>
                    {t("Requested by")}: <b>{r.requested_by}</b> ({r.requested_role})
                  </div>
                  {r.reason && <div className="dim" style={{ fontSize: 12, marginTop: 2 }}>{t("Reason")}: {r.reason}</div>}
                  <div className="faint" style={{ fontSize: 11, marginTop: 4 }}>{new Date(r.created_at).toLocaleString()}</div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button className="btn primary" disabled={busy === r.id} onClick={() => reviewAccess(r.id, "approved")}
                    style={{ fontSize: 12 }}>
                    <CheckCircle size={13} /> {t("Approve")}
                  </button>
                  <button className="btn ghost" disabled={busy === r.id} onClick={() => reviewAccess(r.id, "rejected")}
                    style={{ fontSize: 12 }}>
                    <XCircle size={13} /> {t("Reject")}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
