import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, TrendingUp, TrendingDown, FileDown, MapPin } from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { BarViz, Chip, Loading, Panel, Stat } from "../components";
import { KarnatakaMap } from "../KarnatakaMap";
import { commandBriefing } from "../briefing";

export default function CommandCenter() {
  const { user } = useAuth();
  const { t } = useLang();
  const nav = useNavigate();
  const [d, setD] = useState<any>(null);
  const [map, setMap] = useState<any>(null);
  const [selDistrict, setSelDistrict] = useState<string | null>(null);

  useEffect(() => {
    api.command().then(setD).catch(() => setD({ error: true }));
    api.districtMap().then((r) => setMap(r.districts));
  }, []);

  if (!d) return <Loading label={t("Loading command center…")} />;
  if (d.error) return <Panel title={t("Access restricted")}><p className="dim">{t("Command Center")} — SHO / DSP / Commander.</p></Panel>;

  const k = d.kpis;
  const Trend = k.firs_change >= 0 ? TrendingUp : TrendingDown;

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div className="faint" style={{ fontSize: 13 }}>
          <MapPin size={13} /> {d.district} · <span style={{ textTransform: "capitalize" }}>{d.scope} {t("scope")}</span>
        </div>
        <button className="btn" onClick={() => map && commandBriefing(d, map,
          { full_name: user!.full_name, rank: user!.rank, badge_number: user!.badge_number })}
          disabled={!map}>
          <FileDown size={15} /> {t("Export intelligence brief (PDF)")}
        </button>
      </div>

      <div className="grid cols-4" data-tour="command-kpis">
        <Stat label={t("Total Cases")} value={k.total_cases} sub={`${k.open} ${t("open")}`} />
        <Stat label={t("Clearance Rate")} value={`${k.clearance_rate}%`} color="#24d18b" />
        <Stat label={t("FIRs this month")} value={k.firs_this_month}
          sub={`${k.firs_change >= 0 ? "+" : ""}${k.firs_change}% ${t("vs last month")}`}
          color={k.firs_change >= 0 ? "#ff8a4d" : "#24d18b"} />
        <Stat label={t("Arrests (30d)")} value={k.arrests_month} color="#2f81f7" />
      </div>

      <Panel title={t("Karnataka Crime Hotspot Map")}
        info={{ what: "District incident density projected on Karnataka using real case coordinates. Click a district to focus.", data: "cases lat/lon centroids", brief: "Hotspots & geospatial (#3)" }}>
        {!map ? <Loading label={t("Rendering map…")} /> :
          <KarnatakaMap districts={map} selected={selDistrict} onSelect={setSelDistrict} />}
      </Panel>

      <div className="grid" style={{ gridTemplateColumns: "2fr 1fr" }}>
        <Panel title={t("Intelligence Stream")}
          info={{ what: "Live feed of investigation events across your jurisdiction.", data: "timeline_events" }}>
          <div style={{ maxHeight: 320, overflowY: "auto" }}>
            {d.stream.map((e: any, i: number) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "9px 0", borderBottom: "1px solid var(--border)" }}>
                <div style={{ width: 8, height: 8, marginTop: 5, background:
                  e.severity === "Critical" ? "var(--red)" : e.severity === "High" ? "var(--amber)" : "var(--accent)" }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13 }}><b>{e.title}</b> <Chip>{e.type}</Chip></div>
                  <div className="faint" style={{ fontSize: 11 }}>{e.case} · {e.district} · {e.time?.slice(0, 10)}</div>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={t("Priority Alerts")}
          info={{ what: "Unresolved early-warning alerts in your jurisdiction.", data: "alerts", brief: "Early warning (#8)" }}>
          {d.alerts.length === 0 && <div className="faint">{t("No active alerts.")}</div>}
          {d.alerts.map((a: any) => (
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

      <div className="grid cols-3">
        <Panel title={t("Offender Pool — highest risk")}
          info={{ what: "Top high-risk offenders in scope, ranked by risk score.", data: "behavior_profiles", brief: "Offender profiling (#5)" }}>
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

        <Panel title={t("Predicted Hotspots")}
          info={{ what: "Forecast of likely crime by area and window.", data: "predictions", brief: "Forecasting (#8)" }}>
          {d.predictions.length === 0 && <div className="faint">{t("No forecasts in scope.")}</div>}
          {d.predictions.map((p: any, i: number) => (
            <div key={i} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
                <span><b>{p.crime}</b> · {p.area}</span>
                <Chip kind={p.level}>{Math.round(p.prob * 100)}%</Chip>
              </div>
            </div>
          ))}
        </Panel>

        <Panel title={t("Cases by District")}
          info={{ what: "Incident distribution across your jurisdiction.", data: "cases grouped by district" }}>
          <BarViz data={d.district_breakdown.slice(0, 8)} horizontal color="#a06bff" height={230} />
        </Panel>
      </div>
    </div>
  );
}
