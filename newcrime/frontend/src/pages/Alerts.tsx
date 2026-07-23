import { useEffect, useState, useRef, useCallback } from "react";
import { AlertTriangle, Check, Bell, ChevronDown, ChevronUp, X } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { Chip, Loading, Panel } from "../components";

/* ── Toast notification ───────────────────────────────────────────── */
interface Toast {
  id: number;
  message: string;
  severity: string;
}

function ToastContainer({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div style={{
      position: "fixed", top: 16, right: 16, zIndex: 2000,
      display: "flex", flexDirection: "column", gap: 8, maxWidth: 380,
    }}>
      {toasts.map((t) => (
        <div key={t.id} className="alert-toast" style={{
          display: "flex", alignItems: "center", gap: 10, padding: "12px 14px",
          background: "var(--panel)", border: "1px solid var(--border-strong)",
          borderLeft: `3px solid ${t.severity === "Critical" ? "var(--red)" :
            t.severity === "High" ? "var(--amber)" : "var(--accent)"}`,
          boxShadow: "var(--shadow)",
          animation: "toastSlideIn 0.35s ease-out",
        }}>
          <Bell size={15} style={{
            color: t.severity === "Critical" ? "var(--red)" :
              t.severity === "High" ? "var(--amber)" : "var(--accent)",
            flexShrink: 0,
          }} />
          <div style={{ flex: 1, fontSize: 13 }}>{t.message}</div>
          <X size={14} style={{ cursor: "pointer", flexShrink: 0, color: "var(--text-faint)" }}
            onClick={() => onDismiss(t.id)} />
        </div>
      ))}
      <style>{`
        @keyframes toastSlideIn {
          from { transform: translateX(120%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
        @keyframes toastFadeOut {
          from { opacity: 1; transform: translateX(0); }
          to   { opacity: 0; transform: translateX(60%); }
        }
      `}</style>
    </div>
  );
}

/* ── Audio beep (Web Audio API) ───────────────────────────────────── */
function playAlertBeep() {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = 800;
    gain.gain.value = 0.3;
    osc.start();
    setTimeout(() => { osc.stop(); ctx.close(); }, 150);
  } catch {
    // AudioContext may not be available in all environments
  }
}

/* ── Main component ───────────────────────────────────────────────── */
export default function Alerts() {
  const { t } = useLang();
  const [rows, setRows] = useState<any[] | null>(null);
  const [unresolved, setUnresolved] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [showNotifCenter, setShowNotifCenter] = useState(false);
  const toastIdRef = useRef(0);
  const hasBeepedRef = useRef(false);
  const prevCountRef = useRef<number | null>(null);

  const addToast = useCallback((message: string, severity: string) => {
    const id = ++toastIdRef.current;
    setToasts((prev) => [...prev, { id, message, severity }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const load = () => { setRows(null); api.alerts(unresolved).then(setRows); };
  useEffect(load, [unresolved]);

  // Audio beep on first load if Critical/High alerts exist
  useEffect(() => {
    if (!rows || hasBeepedRef.current) return;
    const hasCriticalHigh = rows.some(
      (a) => !a.resolved && (a.severity === "Critical" || a.severity === "High")
    );
    if (hasCriticalHigh) {
      playAlertBeep();
      hasBeepedRef.current = true;
    }
  }, [rows]);

  // Toast on new alerts arriving (after first load)
  useEffect(() => {
    if (!rows) return;
    const unresolvedCount = rows.filter((a) => !a.resolved).length;
    if (prevCountRef.current !== null && unresolvedCount > prevCountRef.current) {
      const newCount = unresolvedCount - prevCountRef.current;
      addToast(
        `${newCount} ${t("new alert(s) received")}`,
        rows.find((a) => !a.resolved && (a.severity === "Critical" || a.severity === "High"))
          ? "Critical" : "Medium"
      );
    }
    prevCountRef.current = unresolvedCount;
  }, [rows, addToast, t]);

  const resolve = async (id: number) => { await api.resolveAlert(id); load(); };

  // Severity counts for notification center
  const severityCounts = rows ? {
    Critical: rows.filter((a) => !a.resolved && a.severity === "Critical").length,
    High: rows.filter((a) => !a.resolved && a.severity === "High").length,
    Medium: rows.filter((a) => !a.resolved && a.severity === "Medium").length,
    Low: rows.filter((a) => !a.resolved && a.severity === "Low").length,
  } : { Critical: 0, High: 0, Medium: 0, Low: 0 };
  const totalUnresolved = severityCounts.Critical + severityCounts.High +
    severityCounts.Medium + severityCounts.Low;

  if (!rows) return <Loading label={t("Loading alerts...")} />;

  return (
    <div className="grid" style={{ gap: 16 }}>
      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Notification Center toggle */}
      <div style={{
        background: "var(--panel)", border: "1px solid var(--border)", padding: 0,
      }}>
        <button onClick={() => setShowNotifCenter(!showNotifCenter)} style={{
          width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "12px 16px", background: "none", border: "none", color: "var(--text)",
          cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Bell size={16} />
            <span>{t("Notification Center")}</span>
            {totalUnresolved > 0 && (
              <span style={{
                background: "var(--red)", color: "#fff", padding: "1px 7px",
                fontSize: 11, fontWeight: 700, minWidth: 20, textAlign: "center",
              }}>{totalUnresolved}</span>
            )}
          </div>
          {showNotifCenter ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>

        {showNotifCenter && (
          <div style={{
            padding: "0 16px 14px", borderTop: "1px solid var(--border)",
            display: "flex", gap: 16, flexWrap: "wrap", paddingTop: 14,
          }}>
            {(["Critical", "High", "Medium", "Low"] as const).map((sev) => (
              <div key={sev} style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "8px 14px", border: "1px solid var(--border)",
                background: "var(--panel-2)", minWidth: 130,
              }}>
                <span style={{
                  width: 8, height: 8,
                  background: sev === "Critical" ? "var(--red)" :
                    sev === "High" ? "var(--amber)" :
                    sev === "Medium" ? "var(--accent)" : "var(--green)",
                  flexShrink: 0,
                }} />
                <span style={{ fontSize: 12, color: "var(--text-dim)", flex: 1 }}>{t(sev)}</span>
                <span style={{ fontSize: 18, fontWeight: 700 }}>{severityCounts[sev]}</span>
              </div>
            ))}
            <div style={{
              fontSize: 12, color: "var(--text-faint)", display: "flex",
              alignItems: "center", gap: 6,
            }}>
              <AlertTriangle size={13} />
              {t("total unresolved")}: {totalUnresolved}
            </div>
          </div>
        )}
      </div>

      <Panel title={t("Early-warning Alert Feed")} right={
        <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 12 }}>
          <input type="checkbox" checked={unresolved} onChange={(e) => setUnresolved(e.target.checked)}
            style={{ width: 15, height: 15 }} /> {t("unresolved only")}
        </label>
      }>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {rows.length === 0 && <div className="faint center" style={{ padding: 30 }}>{t("No alerts.")}</div>}
          {rows.map((a) => (
            <div key={a.id} style={{ display: "flex", gap: 12, alignItems: "center", padding: "12px 14px",
              border: "1px solid var(--border)", background: "var(--panel-2)",
              opacity: a.resolved ? 0.55 : 1,
              borderLeft: `3px solid ${a.severity === "Critical" ? "var(--red)" :
                a.severity === "High" ? "var(--amber)" : "var(--accent)"}` }}>
              <AlertTriangle size={18} className="dim" />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{a.title}</div>
                <div className="dim" style={{ fontSize: 13, margin: "2px 0" }}>{a.message}</div>
                <div className="faint" style={{ fontSize: 12 }}>
                  {a.district} · {a.alert_type} · {new Date(a.created_at).toLocaleDateString()}
                </div>
              </div>
              <Chip kind={a.severity}>{a.severity}</Chip>
              {a.resolved ? <Chip kind="green">{t("resolved")}</Chip> :
                <button className="btn ghost" onClick={() => resolve(a.id)}>
                  <Check size={14} /> {t("Resolve")}
                </button>}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
