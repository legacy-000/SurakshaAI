import { useEffect, useState } from "react";
import { ScrollText, Eye } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { BarViz, Chip, Loading, Panel, Stat } from "../components";

export default function Audit() {
  const { t } = useLang();
  const [summary, setSummary] = useState<any>(null);
  const [logs, setLogs] = useState<any[] | null>(null);
  const [piiOnly, setPiiOnly] = useState(false);

  useEffect(() => { api.auditSummary().then(setSummary).catch(() => {}); }, []);
  useEffect(() => {
    setLogs(null);
    api.auditLogs({ limit: 150, pii_only: piiOnly || undefined }).then(setLogs).catch(() => setLogs([]));
  }, [piiOnly]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      {summary && (
        <>
          <div className="grid cols-3">
            <Stat label={t("Total Access Events")} value={summary.total} />
            <Stat label={t("PII Accesses")} value={summary.pii_accesses} color="#ff4d5e" />
            <Stat label={t("Roles Active")} value={summary.by_role.length} color="#2f81f7" />
          </div>
          <div className="grid cols-2">
            <Panel title={t("Access by Role")}><BarViz data={summary.by_role} color="#2f81f7" height={220} /></Panel>
            <Panel title={t("Access by Module")}><BarViz data={summary.by_resource} horizontal color="#a06bff" height={220} /></Panel>
          </div>
        </>
      )}

      <Panel title={<span><ScrollText size={13} /> {t("Access Log")}</span> as any}
        right={
          <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 12 }}>
            <input type="checkbox" checked={piiOnly} onChange={(e) => setPiiOnly(e.target.checked)}
              style={{ width: 15, height: 15 }} /> {t("PII accesses only")}
          </label>
        }>
        {!logs ? <Loading /> : (
          <div style={{ overflowX: "auto", maxHeight: 460 }}>
            <table>
              <thead>
                <tr><th>{t("Time")}</th><th>{t("Officer")}</th><th>{t("Role")}</th><th>{t("Action")}</th>
                  <th>{t("Module")}</th><th>{t("Path")}</th><th>{t("Status")}</th><th>{t("PII")}</th></tr>
              </thead>
              <tbody>
                {logs.map((l) => (
                  <tr key={l.id}>
                    <td className="faint mono" style={{ fontSize: 11, whiteSpace: "nowrap" }}>
                      {new Date(l.created_at).toLocaleTimeString()}
                    </td>
                    <td>{l.user_name || "—"}</td>
                    <td className="dim">{l.role}</td>
                    <td><Chip>{l.action}</Chip></td>
                    <td>{l.resource}</td>
                    <td className="faint mono" style={{ fontSize: 11 }}>{l.path}</td>
                    <td className={l.status_code >= 400 ? "" : "dim"}
                      style={l.status_code >= 400 ? { color: "var(--red)" } : {}}>{l.status_code}</td>
                    <td>{l.pii_accessed ? <Chip kind="Critical"><Eye size={11} /> PII</Chip> : ""}</td>
                  </tr>
                ))}
              </tbody>
              {logs.length === 0 && <div className="faint center" style={{ padding: 30 }}>{t("No audit events yet.")}</div>}
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
