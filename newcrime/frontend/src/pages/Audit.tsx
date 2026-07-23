import { Fragment, useEffect, useState, useCallback } from "react";
import { ScrollText, Eye, ChevronDown, ChevronUp, Filter, Monitor, Globe } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { BarViz, Chip, Loading, Panel, Stat } from "../components";

const ACTION_COLORS: Record<string, string> = {
  view: "accent", create: "green", update: "amber", delete: "red",
  login: "accent", upload: "green", approve: "green", reject: "red", export: "amber",
};

export default function Audit() {
  const { t } = useLang();
  const [summary, setSummary] = useState<any>(null);
  const [logs, setLogs] = useState<any[] | null>(null);
  const [piiOnly, setPiiOnly] = useState(false);
  const [actionType, setActionType] = useState("");
  const [resource, setResource] = useState("");
  const [district, setDistrict] = useState("");
  const [userName, setUserName] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => { api.auditSummary().then(setSummary).catch(() => {}); }, []);

  const loadLogs = useCallback(() => {
    setLogs(null);
    const params: Record<string, any> = { limit: 200 };
    if (piiOnly) params.pii_only = true;
    if (actionType) params.action_type = actionType;
    if (resource) params.resource = resource;
    if (district) params.district = district;
    if (userName) params.user_name = userName;
    api.auditLogs(params).then(setLogs).catch(() => setLogs([]));
  }, [piiOnly, actionType, resource, district, userName]);

  useEffect(() => {
    const tm = setTimeout(loadLogs, 300);
    return () => clearTimeout(tm);
  }, [loadLogs]);

  const hasFilters = piiOnly || actionType || resource || district || userName;
  const clearFilters = () => { setPiiOnly(false); setActionType(""); setResource(""); setDistrict(""); setUserName(""); };

  return (
    <div className="grid" style={{ gap: 16 }}>
      {summary && (
        <>
          {summary.scope && summary.scope !== "state" && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 14px",
              background: "rgba(0,209,255,0.08)", border: "1px solid rgba(0,209,255,0.2)",
              borderRadius: 8, fontSize: 12 }}>
              <Globe size={14} style={{ color: "var(--accent)" }} />
              <span>{t("Territory scope")}: <b>{summary.scope}</b></span>
              {summary.scope_districts?.length > 0 && (
                <span className="faint"> — {summary.scope_districts.join(", ")}</span>
              )}
            </div>
          )}
          <div className="grid cols-4">
            <Stat label={t("Total Access Events")} value={summary.total} />
            <Stat label={t("PII Accesses")} value={summary.pii_accesses} color="#ff4d5e" />
            <Stat label={t("Roles Active")} value={summary.by_role.length} color="#2f81f7" />
            <Stat label={t("Districts")} value={summary.by_district?.length || 0} />
          </div>
          <div className="grid cols-2">
            <Panel title={t("Access by Role")}><BarViz data={summary.by_role} color="#2f81f7" height={220} /></Panel>
            <Panel title={t("Access by Module")}><BarViz data={summary.by_resource} horizontal color="#a06bff" height={220} /></Panel>
          </div>
          {summary.by_action_type?.length > 0 && summary.by_district?.length > 0 && (
            <div className="grid cols-2">
              <Panel title={t("By Action Type")}><BarViz data={summary.by_action_type} horizontal color="#48bb78" height={200} /></Panel>
              <Panel title={t("By District")}><BarViz data={summary.by_district} horizontal color="#ed8936" height={200} /></Panel>
            </div>
          )}
        </>
      )}

      <Panel title={<span><ScrollText size={13} /> {t("Access Log")}</span> as any}
        right={
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button className="btn ghost" onClick={() => setShowFilters(!showFilters)}
              style={hasFilters ? { borderColor: "var(--accent)", color: "var(--accent)", fontSize: 12 } : { fontSize: 12 }}>
              <Filter size={12} /> {t("Filters")} {hasFilters ? "(active)" : ""}
            </button>
            {hasFilters && <button className="btn ghost" onClick={clearFilters} style={{ fontSize: 11 }}>{t("Clear")}</button>}
          </div>
        }>

        {showFilters && (
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", padding: "10px 0", borderBottom: "1px solid var(--border)", marginBottom: 10, alignItems: "end" }}>
            <div>
              <label className="faint" style={{ fontSize: 10, display: "block", marginBottom: 2 }}>{t("Action Type")}</label>
              <select value={actionType} onChange={(e) => setActionType(e.target.value)} style={{ fontSize: 12, minWidth: 110 }}>
                <option value="">{t("All")}</option>
                {["view", "create", "update", "delete", "login", "upload", "approve", "reject", "export"].map(
                  a => <option key={a} value={a}>{a}</option>
                )}
              </select>
            </div>
            <div>
              <label className="faint" style={{ fontSize: 10, display: "block", marginBottom: 2 }}>{t("Module")}</label>
              <select value={resource} onChange={(e) => setResource(e.target.value)} style={{ fontSize: 12, minWidth: 120 }}>
                <option value="">{t("All")}</option>
                {(summary?.by_resource || []).map((r: any) => <option key={r.label} value={r.label}>{r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="faint" style={{ fontSize: 10, display: "block", marginBottom: 2 }}>{t("District")}</label>
              <select value={district} onChange={(e) => setDistrict(e.target.value)} style={{ fontSize: 12, minWidth: 120 }}>
                <option value="">{t("All")}</option>
                {(summary?.by_district || []).map((d: any) => <option key={d.label} value={d.label}>{d.label}</option>)}
              </select>
            </div>
            <div>
              <label className="faint" style={{ fontSize: 10, display: "block", marginBottom: 2 }}>{t("Officer")}</label>
              <input placeholder={t("Search...")} value={userName} onChange={(e) => setUserName(e.target.value)}
                style={{ fontSize: 12, width: 130 }} />
            </div>
            <label style={{ display: "flex", gap: 4, alignItems: "center", fontSize: 11, cursor: "pointer" }}>
              <input type="checkbox" checked={piiOnly} onChange={(e) => setPiiOnly(e.target.checked)} />
              {t("PII only")}
            </label>
          </div>
        )}

        {!logs ? <Loading /> : (
          <div style={{ overflowX: "auto", maxHeight: 520 }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: 20 }}></th>
                  <th>{t("Time")}</th>
                  <th>{t("Officer")}</th>
                  <th>{t("Role")}</th>
                  <th>{t("Type")}</th>
                  <th>{t("Module")}</th>
                  <th>{t("District")}</th>
                  <th>{t("Status")}</th>
                  <th>{t("PII")}</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((l) => (
                  <Fragment key={l.id}>
                    <tr style={{ cursor: "pointer" }} onClick={() => setExpanded(expanded === l.id ? null : l.id)}>
                      <td style={{ padding: "4px 2px" }}>
                        {expanded === l.id ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                      </td>
                      <td className="faint mono" style={{ fontSize: 11, whiteSpace: "nowrap" }}>
                        {new Date(l.created_at).toLocaleString()}
                      </td>
                      <td style={{ fontSize: 12 }}>{l.user_name || "—"}</td>
                      <td className="dim" style={{ fontSize: 11 }}>{l.role}</td>
                      <td>
                        <Chip kind={ACTION_COLORS[l.action_type] || "accent"}>
                          {l.action_type || l.action}
                        </Chip>
                      </td>
                      <td style={{ fontSize: 12 }}>{l.resource}</td>
                      <td className="dim" style={{ fontSize: 11 }}>{l.district || "—"}</td>
                      <td className={l.status_code >= 400 ? "" : "dim"}
                        style={l.status_code >= 400 ? { color: "var(--red, #e53e3e)" } : {}}>{l.status_code}</td>
                      <td>{l.pii_accessed ? <Chip kind="Critical"><Eye size={11} /> PII</Chip> : ""}</td>
                    </tr>
                    {expanded === l.id && (
                      <tr>
                        <td colSpan={9} style={{ background: "var(--panel-2)", padding: "10px 16px" }}>
                          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr auto 1fr", gap: "4px 16px", fontSize: 12 }}>
                            <span className="faint">{t("Path")}:</span>
                            <span className="mono" style={{ fontSize: 11 }}>{l.path}</span>
                            <span className="faint">{t("Method")}:</span>
                            <span><Chip>{l.action}</Chip></span>
                            <span className="faint">{t("IP Address")}:</span>
                            <span className="mono" style={{ fontSize: 11 }}>{l.ip_address || "—"}</span>
                            <span className="faint">{t("Session ID")}:</span>
                            <span className="mono" style={{ fontSize: 11 }}>{l.session_id || "—"}</span>
                            <span className="faint">{t("User Agent")}:</span>
                            <span className="dim" style={{ fontSize: 10, gridColumn: "2 / 5", wordBreak: "break-all" }}>
                              {l.user_agent || "—"}
                            </span>
                            {l.detail && <Fragment>
                              <span className="faint">{t("Detail")}:</span>
                              <span style={{ gridColumn: "2 / 5" }}>{l.detail}</span>
                            </Fragment>}
                            {l.prev_value && <Fragment>
                              <span className="faint">{t("Previous Value")}:</span>
                              <span style={{ gridColumn: "2 / 5", fontSize: 11 }}>{l.prev_value}</span>
                            </Fragment>}
                            {l.new_value && <Fragment>
                              <span className="faint">{t("New Value")}:</span>
                              <span style={{ gridColumn: "2 / 5", fontSize: 11 }}>{l.new_value}</span>
                            </Fragment>}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
            {logs.length === 0 && <div className="faint center" style={{ padding: 30 }}>{t("No audit events yet.")}</div>}
          </div>
        )}
      </Panel>
    </div>
  );
}
