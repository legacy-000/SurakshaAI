import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle, TrendingUp, TrendingDown, FileDown, MapPin, Shield,
  Brain, Lightbulb, Globe, Target, Users, BarChart3, Building2,
  ChevronRight, Zap, Eye, Clock, AlertCircle, Activity, Award,
  Briefcase, CheckCircle, XCircle, Layers, Crosshair,
} from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { BarViz, Chip, Loading, Panel, Stat } from "../components";
import { KarnatakaMap } from "../KarnatakaMap";
import { commandBriefing } from "../briefing";

const LEVEL_LABELS: Record<string, string> = {
  state: "State Command Center — DG & IGP",
  range: "Range Command Center — IG/DIG",
  district: "District Command Center — SP",
  subdivision: "Subdivision Command Center — DySP/ACP",
  station: "Station Command Center — SHO/PI",
};

const LEVEL_SCOPE_LABELS: Record<string, string> = {
  state: "All Karnataka",
  range: "Range Jurisdiction",
  district: "District Jurisdiction",
  subdivision: "Subdivision Jurisdiction",
  station: "Station Jurisdiction",
};

const PRIORITY_COLORS: Record<string, string> = {
  Critical: "var(--red)",
  High: "var(--amber)",
  Medium: "var(--accent)",
  Low: "var(--green)",
};

export default function CommandCenter() {
  const { user } = useAuth();
  const { t } = useLang();
  const nav = useNavigate();
  const [d, setD] = useState<any>(null);
  const [map, setMap] = useState<any>(null);
  const [selDistrict, setSelDistrict] = useState<string | null>(null);

  useEffect(() => {
    api.command().then(setD).catch(() => setD({ error: true }));
    api.districtMap().then((r) => setMap(r.districts)).catch(() => {});
  }, []);

  if (!d) return <Loading label={t("Loading command center…")} />;
  if (d.error)
    return (
      <Panel title={t("Access restricted")}>
        <p className="dim">{t("Command Center access requires command authority.")}</p>
      </Panel>
    );

  const k = d.kpis;
  const level = d.command_level || "station";
  const Trend = k.firs_change >= 0 ? TrendingUp : TrendingDown;
  const isState = level === "state";
  const isRange = level === "range";
  const isDistrict = level === "district";
  const isSubdivision = level === "subdivision";
  const isStation = level === "station";
  const showMap = isState || isRange || isDistrict;

  return (
    <div className="grid" style={{ gap: 16 }}>
      {/* ── Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Shield size={18} style={{ color: "var(--accent)" }} />
            <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
              {t(LEVEL_LABELS[level] || "Command Center")}
            </h3>
          </div>
          <div className="faint" style={{ fontSize: 12, marginTop: 4, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <MapPin size={12} />
            <span style={{ fontWeight: 600 }}>{d.district}</span>
            {d.subdivision && <span>· {d.subdivision}</span>}
            {d.range_name && <span>· {d.range_name} {t("Range")}</span>}
            <span style={{ background: "rgba(0,209,255,0.12)", padding: "2px 8px", fontSize: 10, fontWeight: 600, letterSpacing: 0.5, textTransform: "uppercase" }}>
              {t(LEVEL_SCOPE_LABELS[level] || d.scope)}
            </span>
          </div>
        </div>
        <button className="btn" onClick={() => map && commandBriefing(d, map,
          { full_name: user!.full_name, rank: user!.rank, badge_number: user!.badge_number })}
          disabled={!map}>
          <FileDown size={15} /> {t("Export intelligence brief (PDF)")}
        </button>
      </div>

      {/* ── Primary KPIs ── */}
      <div className="grid cols-4" data-tour="command-kpis">
        <Stat label={t("Total Cases")} value={k.total_cases} sub={`${k.open} ${t("open")}`} />
        <Stat label={t("Clearance Rate")} value={`${k.clearance_rate}%`} color="#24d18b" />
        <Stat label={t("FIRs this month")} value={k.firs_this_month}
          sub={`${k.firs_change >= 0 ? "+" : ""}${k.firs_change}% ${t("vs last month")}`}
          color={k.firs_change >= 0 ? "#ff8a4d" : "#24d18b"} />
        <Stat label={t("Arrests (30d)")} value={k.arrests_month} color="#2f81f7" />
      </div>

      {/* ── Secondary KPIs ── */}
      <div className="grid cols-4">
        <Stat label={t("Pending Cases")} value={k.pending_cases} color="#ffb020" />
        <Stat label={t("Chargesheet Rate")} value={`${k.chargesheet_rate}%`} color="#a06bff" />
        <Stat label={t("Active Investigations")} value={d.investigation_summary?.active || k.open} color="#00d1ff" />
        <Stat label={t("Emergency Alerts")} value={d.alerts?.length || 0} color="#ff4d5e" />
      </div>

      {/* ── Investigation Progress ── */}
      {d.investigation_summary && (
        <Panel title={<span><Briefcase size={14} /> {t("Investigation Progress")}</span> as any}>
          <div className="grid cols-4" style={{ gap: 12 }}>
            <div style={{ textAlign: "center", padding: "12px 8px", border: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <Activity size={18} style={{ color: "#00d1ff", marginBottom: 4 }} />
              <div style={{ fontSize: 22, fontWeight: 700, color: "#00d1ff" }}>{d.investigation_summary.active}</div>
              <div className="faint" style={{ fontSize: 11 }}>{t("Active")}</div>
            </div>
            <div style={{ textAlign: "center", padding: "12px 8px", border: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <Clock size={18} style={{ color: "#ffb020", marginBottom: 4 }} />
              <div style={{ fontSize: 22, fontWeight: 700, color: "#ffb020" }}>{d.investigation_summary.pending}</div>
              <div className="faint" style={{ fontSize: 11 }}>{t("Pending")}</div>
            </div>
            <div style={{ textAlign: "center", padding: "12px 8px", border: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <CheckCircle size={18} style={{ color: "#24d18b", marginBottom: 4 }} />
              <div style={{ fontSize: 22, fontWeight: 700, color: "#24d18b" }}>{d.investigation_summary.solved}</div>
              <div className="faint" style={{ fontSize: 11 }}>{t("Solved")}</div>
            </div>
            <div style={{ textAlign: "center", padding: "12px 8px", border: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <XCircle size={18} style={{ color: "var(--text-faint)", marginBottom: 4 }} />
              <div style={{ fontSize: 22, fontWeight: 700 }}>{d.investigation_summary.cold}</div>
              <div className="faint" style={{ fontSize: 11 }}>{t("Cold Cases")}</div>
            </div>
          </div>
          <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 10 }}>
            <div className="faint" style={{ fontSize: 12 }}>{t("Avg. Progress")}</div>
            <div style={{ flex: 1, height: 8, background: "var(--border)", overflow: "hidden" }}>
              <div style={{ width: `${d.investigation_summary.avg_progress}%`, height: "100%", background: "#00d1ff" }} />
            </div>
            <div style={{ fontSize: 13, fontWeight: 600 }}>{d.investigation_summary.avg_progress}%</div>
          </div>
        </Panel>
      )}

      {/* ── Map (state/range/district levels) ── */}
      {showMap && (
        <Panel title={<span><Globe size={14} /> {isState ? t("State Crime Heatmap") : t("Jurisdiction Crime Heatmap")}</span> as any}>
          {!map ? <Loading label={t("Rendering map…")} /> :
            <KarnatakaMap districts={map} selected={selDistrict} onSelect={setSelDistrict} />}
        </Panel>
      )}

      {/* ── District Ranking (state/range levels) ── */}
      {d.district_ranking && d.district_ranking.length > 0 && (
        <Panel title={<span><Award size={14} /> {t("District Ranking")}</span> as any}>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "8px 12px", fontWeight: 600, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>#</th>
                  <th style={{ textAlign: "left", padding: "8px 12px", fontWeight: 600, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("District")}</th>
                  <th style={{ textAlign: "right", padding: "8px 12px", fontWeight: 600, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Total Cases")}</th>
                  <th style={{ textAlign: "right", padding: "8px 12px", fontWeight: 600, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Solved")}</th>
                  <th style={{ textAlign: "right", padding: "8px 12px", fontWeight: 600, fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Clearance Rate")}</th>
                </tr>
              </thead>
              <tbody>
                {d.district_ranking.map((r: any, i: number) => (
                  <tr key={r.district} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "8px 12px", fontWeight: 600 }}>{i + 1}</td>
                    <td style={{ padding: "8px 12px" }}>
                      <span style={{ fontWeight: 600 }}>{r.district}</span>
                    </td>
                    <td style={{ padding: "8px 12px", textAlign: "right" }}>{r.total}</td>
                    <td style={{ padding: "8px 12px", textAlign: "right" }}>{r.solved}</td>
                    <td style={{ padding: "8px 12px", textAlign: "right" }}>
                      <span style={{
                        color: r.clearance > 50 ? "#24d18b" : r.clearance > 30 ? "#ffb020" : "#ff4d5e",
                        fontWeight: 600,
                      }}>
                        {r.clearance}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* ── AI Intelligence ── */}
      {d.ai_insights && d.ai_insights.length > 0 && (
        <Panel title={<span><Brain size={14} /> {t("AI Intelligence")}</span> as any}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
            {d.ai_insights.map((ins: any, i: number) => (
              <div key={i} style={{
                padding: "14px 16px", border: "1px solid var(--border)",
                background: "var(--panel-2)",
                borderLeft: `3px solid ${PRIORITY_COLORS[ins.severity] || "var(--accent)"}`,
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 8 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.4 }}>{ins.title}</div>
                  <Chip kind={ins.severity}>{ins.severity}</Chip>
                </div>
                <div className="dim" style={{ fontSize: 12, marginTop: 6, lineHeight: 1.5 }}>{ins.detail}</div>
                <div className="faint" style={{ fontSize: 10, marginTop: 6 }}>
                  <Eye size={10} /> {ins.category}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* ── AI Recommended Actions ── */}
      {d.ai_recommendations && d.ai_recommendations.length > 0 && (
        <Panel title={<span><Lightbulb size={14} /> {t("AI Recommended Actions")}</span> as any}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {d.ai_recommendations.map((rec: any, i: number) => (
              <div key={i} style={{
                display: "flex", gap: 14, alignItems: "start", padding: "12px 14px",
                border: "1px solid var(--border)", background: "var(--panel-2)",
              }}>
                <div style={{
                  width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center",
                  background: `${PRIORITY_COLORS[rec.priority] || "var(--accent)"}15`,
                  border: `1px solid ${PRIORITY_COLORS[rec.priority] || "var(--accent)"}40`,
                  flexShrink: 0,
                }}>
                  <Zap size={15} style={{ color: PRIORITY_COLORS[rec.priority] || "var(--accent)" }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.4 }}>{rec.action}</div>
                  <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>{rec.impact}</div>
                  <div style={{ display: "flex", gap: 10, marginTop: 6, flexWrap: "wrap" }}>
                    <span className="faint" style={{ fontSize: 11 }}>
                      <Target size={10} /> {t("Priority")}: <b style={{ color: PRIORITY_COLORS[rec.priority] }}>{rec.priority}</b>
                    </span>
                    <span className="faint" style={{ fontSize: 11 }}>
                      {t("Risk Score")}: {rec.risk_score}
                    </span>
                    <span className="faint" style={{ fontSize: 11 }}>
                      {t("AI Confidence")}: {Math.round((rec.confidence || 0) * 100)}%
                    </span>
                    {rec.category && <Chip kind="accent">{rec.category}</Chip>}
                  </div>
                </div>
                <ChevronRight size={16} className="faint" style={{ marginTop: 4 }} />
              </div>
            ))}
          </div>
        </Panel>
      )}

      {/* ── Neighboring Jurisdiction Intelligence ── */}
      {d.neighbor_intel && (
        <Panel title={<span><Globe size={14} /> {isState
          ? t("Statewide Cross-Border Intelligence")
          : t("Neighboring Jurisdiction Intelligence")
        }</span> as any}>
          {/* Cross-border alerts */}
          {d.neighbor_intel.cross_border_alerts?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.8, color: "var(--text-faint)", fontWeight: 600, marginBottom: 8 }}>
                {t("Cross-Border Alerts")}
              </div>
              {d.neighbor_intel.cross_border_alerts.map((a: any, i: number) => (
                <div key={i} style={{
                  display: "flex", gap: 10, padding: "10px 12px", marginBottom: 6,
                  border: "1px solid var(--border)", background: "var(--panel-2)",
                  borderLeft: `3px solid ${PRIORITY_COLORS[a.severity] || "var(--accent)"}`,
                }}>
                  <AlertCircle size={15} style={{ color: PRIORITY_COLORS[a.severity], marginTop: 1, flexShrink: 0 }} />
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{a.title}</div>
                    <div className="dim" style={{ fontSize: 12, marginTop: 2 }}>{a.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Shared suspects */}
          {d.neighbor_intel.shared_suspects > 0 && (
            <div style={{
              display: "inline-flex", alignItems: "center", gap: 8, padding: "8px 14px",
              background: "rgba(255,77,94,0.08)", border: "1px solid rgba(255,77,94,0.25)",
              marginBottom: 16, fontSize: 13,
            }}>
              <Users size={14} style={{ color: "var(--red)" }} />
              <b>{d.neighbor_intel.shared_suspects}</b> {t("suspects operate across jurisdiction boundaries")}
            </div>
          )}

          {/* Neighbor district summaries */}
          {d.neighbor_intel.neighbor_summary?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.8, color: "var(--text-faint)", fontWeight: 600, marginBottom: 8 }}>
                {isState ? t("Top Cross-Border Hotspot Districts") : t("Neighboring Districts")}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))", gap: 10 }}>
                {d.neighbor_intel.neighbor_summary.map((ns: any) => (
                  <div key={ns.district} style={{
                    padding: "12px 14px", border: "1px solid var(--border)", background: "var(--panel-2)",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>
                        <Building2 size={13} style={{ marginRight: 6 }} />
                        {ns.district}
                      </div>
                      <Chip kind="accent">{ns.total} {t("cases")}</Chip>
                    </div>
                    {ns.cross_border_suspects != null && (
                      <div style={{ fontSize: 11, color: "var(--red)", marginTop: 4, fontWeight: 600 }}>
                        <Crosshair size={10} /> {ns.cross_border_suspects} {t("cross-border suspects")}
                      </div>
                    )}
                    {ns.top_crimes && (
                      <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                        {ns.top_crimes.map((tc: any, j: number) => (
                          <span key={j} className="faint" style={{ fontSize: 11 }}>
                            {tc.crime}: {tc.count}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </Panel>
      )}

      {/* ── Live Intelligence Stream + Priority Alerts ── */}
      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr" }}>
        <Panel title={<span><Activity size={14} /> {t("Live Intelligence Feed")}</span> as any}>
          <div style={{ maxHeight: 360, overflowY: "auto" }}>
            {d.stream.map((e: any, i: number) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "9px 0", borderBottom: "1px solid var(--border)" }}>
                <div style={{ width: 8, height: 8, marginTop: 5, borderRadius: "50%", background:
                  e.severity === "Critical" ? "var(--red)" : e.severity === "High" ? "var(--amber)" : "var(--accent)",
                  boxShadow: e.severity === "Critical" ? "0 0 6px var(--red)" : undefined,
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13 }}><b>{e.title}</b> <Chip>{e.type}</Chip></div>
                  <div className="faint" style={{ fontSize: 11 }}>{e.case} · {e.district} · {e.time?.slice(0, 10)}</div>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={<span><AlertTriangle size={14} /> {t("Priority Alerts")}</span> as any}>
          {(!d.alerts || d.alerts.length === 0) && <div className="faint">{t("No active alerts.")}</div>}
          {d.alerts?.map((a: any) => (
            <div key={a.id} style={{ display: "flex", gap: 8, alignItems: "start", padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <AlertTriangle size={14} className="dim" style={{ marginTop: 2 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{a.title}</div>
                <div className="faint" style={{ fontSize: 11 }}>{a.district} · {a.type}</div>
              </div>
              <Chip kind={a.severity}>{a.severity}</Chip>
            </div>
          ))}
        </Panel>
      </div>

      {/* ── Offenders + Predictions + Cases Breakdown ── */}
      <div className="grid cols-3">
        <Panel title={<span><Users size={14} /> {t("Offender Pool — highest risk")}</span> as any}>
          {d.offenders.map((o: any) => (
            <div key={o.id} onClick={() => user?.permissions.screens.includes("profiling") && nav(`/offender/${o.id}`)}
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "8px 0", borderBottom: "1px solid var(--border)",
                cursor: user?.permissions.screens.includes("profiling") ? "pointer" : "default" }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{o.name}</div>
                <div className="faint" style={{ fontSize: 11 }}>{o.district}</div>
              </div>
              <Chip kind={o.band}>{o.risk} · {o.band}</Chip>
            </div>
          ))}
        </Panel>

        <Panel title={<span><Target size={14} /> {t("Predicted Hotspots")}</span> as any}>
          {(!d.predictions || d.predictions.length === 0) && <div className="faint">{t("No forecasts in scope.")}</div>}
          {d.predictions?.map((p: any, i: number) => (
            <div key={i} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                <span><b>{p.crime}</b> · {p.area}</span>
                <Chip kind={p.level}>{Math.round(p.prob * 100)}%</Chip>
              </div>
            </div>
          ))}
        </Panel>

        <Panel title={<span><BarChart3 size={14} /> {isState || isRange ? t("Cases by District") : t("Cases by Area")}</span> as any}>
          <BarViz data={(d.district_breakdown || []).slice(0, 8)} horizontal color="#a06bff" height={230} />
        </Panel>
      </div>

      {/* ── Station Hotspot Map (district/subdivision/station/range levels) ── */}
      {d.station_hotspots && d.station_hotspots.hotspots.length > 0 && (
        <Panel title={<span><MapPin size={14} /> {t("Sub-District Hotspot Analysis")}</span> as any}>
          {/* Emerging hotspot alert banner */}
          {d.station_hotspots.emerging?.length > 0 && (
            <div style={{
              padding: "10px 14px", marginBottom: 14,
              background: "rgba(255,77,94,0.08)", border: "1px solid rgba(255,77,94,0.25)",
              display: "flex", alignItems: "center", gap: 8, fontSize: 13,
            }}>
              <AlertCircle size={15} style={{ color: "var(--red)", flexShrink: 0 }} />
              <span><b>{d.station_hotspots.emerging.length}</b> {t("emerging hotspots detected")} — {t("crime rising in")} {d.station_hotspots.emerging.map((e: any) => e.station).join(", ")}</span>
            </div>
          )}

          {/* Hotspot scatter visualization */}
          <div style={{ position: "relative", border: "1px solid var(--border)", background: "var(--panel-2)", padding: 16, marginBottom: 14 }}>
            <svg viewBox="0 0 600 280" style={{ width: "100%", height: "auto" }}>
              {/* Grid lines */}
              {[0, 1, 2, 3, 4].map(i => (
                <line key={`g${i}`} x1={60} y1={20 + i * 60} x2={590} y2={20 + i * 60}
                  stroke="var(--border)" strokeWidth={0.5} strokeDasharray="4 4" />
              ))}
              {/* Hotspot bubbles */}
              {d.station_hotspots.hotspots.map((h: any, i: number) => {
                const x = 80 + (i % 5) * 105;
                const y = 50 + Math.floor(i / 5) * 110;
                const r = Math.max(18, Math.min(42, h.heat_score * 0.45));
                const color = h.heat_score >= 70 ? "#ff4d5e" : h.heat_score >= 40 ? "#ffb020" : "#00d1ff";
                return (
                  <g key={i}>
                    <circle cx={x} cy={y} r={r} fill={`${color}25`} stroke={color} strokeWidth={1.5} />
                    <circle cx={x} cy={y} r={r * 0.6} fill={`${color}50`} />
                    <text x={x} y={y - r - 6} textAnchor="middle" fill="var(--text)" fontSize={10} fontWeight={600}>
                      {h.station.replace(" PS", "")}
                    </text>
                    <text x={x} y={y + 4} textAnchor="middle" fill="var(--text)" fontSize={12} fontWeight={700}>
                      {h.cases_30d}
                    </text>
                    {/* Trend arrow */}
                    <text x={x + r + 4} y={y + 4} fontSize={11} fill={h.trend === "rising" ? "#ff4d5e" : h.trend === "falling" ? "#24d18b" : "var(--text-faint)"}>
                      {h.trend === "rising" ? "▲" : h.trend === "falling" ? "▼" : "–"}
                    </text>
                  </g>
                );
              })}
              {/* Legend */}
              <circle cx={80} cy={268} r={6} fill="#ff4d5e25" stroke="#ff4d5e" strokeWidth={1} />
              <text x={92} y={272} fill="var(--text-faint)" fontSize={9}>{t("High Risk")}</text>
              <circle cx={160} cy={268} r={6} fill="#ffb02025" stroke="#ffb020" strokeWidth={1} />
              <text x={172} y={272} fill="var(--text-faint)" fontSize={9}>{t("Medium")}</text>
              <circle cx={230} cy={268} r={6} fill="#00d1ff25" stroke="#00d1ff" strokeWidth={1} />
              <text x={242} y={272} fill="var(--text-faint)" fontSize={9}>{t("Low")}</text>
              <text x={310} y={272} fill="var(--text-faint)" fontSize={9}>▲ {t("Rising")}  ▼ {t("Falling")}  – {t("Stable")}</text>
            </svg>
          </div>

          {/* Hotspot details table */}
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--border)" }}>
                  <th style={{ textAlign: "left", padding: "6px 10px", fontWeight: 600, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Station")}</th>
                  <th style={{ textAlign: "center", padding: "6px 10px", fontWeight: 600, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Cases (30d)")}</th>
                  <th style={{ textAlign: "center", padding: "6px 10px", fontWeight: 600, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Trend")}</th>
                  <th style={{ textAlign: "center", padding: "6px 10px", fontWeight: 600, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Heat Score")}</th>
                  <th style={{ textAlign: "left", padding: "6px 10px", fontWeight: 600, fontSize: 10, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--text-faint)" }}>{t("Top Crimes")}</th>
                </tr>
              </thead>
              <tbody>
                {d.station_hotspots.hotspots.map((h: any) => (
                  <tr key={h.station} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "8px 10px", fontWeight: 600 }}>
                      <MapPin size={11} style={{ marginRight: 4, color: h.heat_score >= 70 ? "#ff4d5e" : h.heat_score >= 40 ? "#ffb020" : "#00d1ff" }} />
                      {h.station}
                    </td>
                    <td style={{ textAlign: "center", padding: "8px 10px" }}>{h.cases_30d}</td>
                    <td style={{ textAlign: "center", padding: "8px 10px" }}>
                      <span style={{
                        display: "inline-flex", alignItems: "center", gap: 4,
                        color: h.trend === "rising" ? "#ff4d5e" : h.trend === "falling" ? "#24d18b" : "var(--text-faint)",
                        fontWeight: 600,
                      }}>
                        {h.trend === "rising" ? <TrendingUp size={12} /> : h.trend === "falling" ? <TrendingDown size={12} /> : "–"}
                        {h.trend_pct > 0 ? "+" : ""}{h.trend_pct}%
                      </span>
                    </td>
                    <td style={{ textAlign: "center", padding: "8px 10px" }}>
                      <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
                        <div style={{ width: 40, height: 6, background: "var(--border)", overflow: "hidden" }}>
                          <div style={{ width: `${h.heat_score}%`, height: "100%",
                            background: h.heat_score >= 70 ? "#ff4d5e" : h.heat_score >= 40 ? "#ffb020" : "#00d1ff" }} />
                        </div>
                        <span style={{ fontSize: 11, fontWeight: 600 }}>{h.heat_score}</span>
                      </div>
                    </td>
                    <td style={{ padding: "8px 10px" }}>
                      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                        {h.top_crimes.map((tc: any, j: number) => (
                          <span key={j} className="faint" style={{ fontSize: 10 }}>{tc.crime}({tc.count})</span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {/* ── Forecast Analysis ── */}
      {d.forecast_analysis && (
        <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
          {/* Forecasts */}
          <Panel title={<span><Target size={14} /> {t("Crime Forecast Analysis")}</span> as any}>
            {d.forecast_analysis.forecasts.length === 0 && <div className="faint">{t("No forecasts in scope.")}</div>}
            {/* Risk summary bar */}
            {d.forecast_analysis.total_forecasts > 0 && (
              <div style={{ display: "flex", gap: 10, marginBottom: 12, flexWrap: "wrap" }}>
                {(["Critical", "High", "Medium", "Low"] as const).map(level => (
                  d.forecast_analysis.risk_summary[level] > 0 && (
                    <div key={level} style={{
                      display: "flex", alignItems: "center", gap: 4, padding: "4px 10px",
                      border: `1px solid ${PRIORITY_COLORS[level]}40`,
                      background: `${PRIORITY_COLORS[level]}10`, fontSize: 12,
                    }}>
                      <div style={{ width: 8, height: 8, background: PRIORITY_COLORS[level] }} />
                      <span style={{ fontWeight: 600 }}>{d.forecast_analysis.risk_summary[level]}</span>
                      <span className="faint">{level}</span>
                    </div>
                  )
                ))}
              </div>
            )}
            <div style={{ maxHeight: 340, overflowY: "auto" }}>
              {d.forecast_analysis.forecasts.map((f: any, i: number) => (
                <div key={i} style={{
                  padding: "10px 12px", marginBottom: 6,
                  border: "1px solid var(--border)", background: "var(--panel-2)",
                  borderLeft: `3px solid ${PRIORITY_COLORS[f.risk_level] || "var(--accent)"}`,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>
                        {f.crime_type} — {f.area}
                      </div>
                      <div className="faint" style={{ fontSize: 11, marginTop: 2 }}>
                        {f.window_start} → {f.window_end}
                      </div>
                    </div>
                    <div style={{
                      padding: "4px 10px", fontWeight: 700, fontSize: 14,
                      color: PRIORITY_COLORS[f.risk_level],
                      background: `${PRIORITY_COLORS[f.risk_level]}12`,
                    }}>
                      {f.probability}%
                    </div>
                  </div>
                  {f.factors.length > 0 && (
                    <div style={{ display: "flex", gap: 4, marginTop: 6, flexWrap: "wrap" }}>
                      {f.factors.map((fac: string, j: number) => (
                        <span key={j} style={{
                          fontSize: 10, padding: "2px 6px",
                          background: "rgba(0,209,255,0.08)", border: "1px solid rgba(0,209,255,0.2)",
                          color: "var(--text-dim)",
                        }}>{fac}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Panel>

          {/* Crime Trend Analysis */}
          <Panel title={<span><TrendingUp size={14} /> {t("Crime Trend Analysis (30d)")}</span> as any}>
            {d.forecast_analysis.crime_trends.map((ct: any, i: number) => (
              <div key={i} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "8px 0", borderBottom: "1px solid var(--border)",
              }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{ct.crime_type}</div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div className="faint" style={{ fontSize: 11 }}>
                    {ct.previous} → {ct.current}
                  </div>
                  <span style={{
                    display: "inline-flex", alignItems: "center", gap: 3, fontWeight: 600, fontSize: 12,
                    padding: "2px 8px",
                    color: ct.trend === "rising" ? "#ff4d5e" : ct.trend === "falling" ? "#24d18b" : "var(--text-faint)",
                    background: ct.trend === "rising" ? "rgba(255,77,94,0.1)" : ct.trend === "falling" ? "rgba(36,209,139,0.1)" : "transparent",
                  }}>
                    {ct.trend === "rising" ? <TrendingUp size={11} /> : ct.trend === "falling" ? <TrendingDown size={11} /> : null}
                    {ct.change_pct > 0 ? "+" : ""}{ct.change_pct}%
                  </span>
                </div>
              </div>
            ))}
          </Panel>
        </div>
      )}

      {/* ── Crime Type Distribution + Station Performance ── */}
      <div className="grid" style={{ gridTemplateColumns: d.station_performance?.length ? "1fr 1fr" : "1fr" }}>
        {d.crime_type_breakdown && d.crime_type_breakdown.length > 0 && (
          <Panel title={<span><Layers size={14} /> {t("Crime Type Distribution")}</span> as any}>
            <BarViz data={d.crime_type_breakdown.slice(0, 8)} horizontal color="#00d1ff" height={250} />
          </Panel>
        )}

        {d.station_performance && d.station_performance.length > 0 && (
          <Panel title={<span><Building2 size={14} /> {t("Station Performance")}</span> as any}>
            <BarViz data={d.station_performance.slice(0, 8)} horizontal color="#24d18b" height={250} />
          </Panel>
        )}
      </div>
    </div>
  );
}
