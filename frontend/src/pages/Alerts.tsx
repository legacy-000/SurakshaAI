import { useEffect, useState } from "react";
import { AlertTriangle, Check } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { Chip, Loading, Panel } from "../components";

export default function Alerts() {
  const { t } = useLang();
  const [rows, setRows] = useState<any[] | null>(null);
  const [unresolved, setUnresolved] = useState(false);

  const load = () => { setRows(null); api.alerts(unresolved).then(setRows); };
  useEffect(load, [unresolved]);

  const resolve = async (id: number) => { await api.resolveAlert(id); load(); };

  if (!rows) return <Loading label={t("Loading alerts…")} />;

  return (
    <div className="grid" style={{ gap: 16 }}>
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
