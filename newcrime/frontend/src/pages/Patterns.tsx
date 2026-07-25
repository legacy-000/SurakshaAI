import { useEffect, useState } from "react";
import { api } from "../api";
import { useLang } from "../context";
import { BarViz, LineViz, Loading, Panel, Chip } from "../components";

export default function Patterns() {
  const { t } = useLang();
  const [trend, setTrend] = useState<any[]>([]);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [temporal, setTemporal] = useState<any>(null);
  const [patterns, setPatterns] = useState<any[]>([]);
  const [types, setTypes] = useState<string[]>([]);
  const [crime, setCrime] = useState("");

  useEffect(() => {
    api.caseFilters().then((f) => setTypes(f.crime_types));
    api.temporal().then(setTemporal);
    api.patterns().then(setPatterns);
  }, []);
  useEffect(() => {
    api.trend(crime).then(setTrend);
    api.hotspots(crime).then(setHotspots);
  }, [crime]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <Panel title={t("Crime Analytics")} right={
        <select value={crime} onChange={(e) => setCrime(e.target.value)}>
          <option value="">{t("All crime types")}</option>
          {types.map((tp) => <option key={tp} value={tp}>{tp}</option>)}
        </select>
      }>
        <div className="grid cols-2">
          <div>
            <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>{t("TREND OVER TIME")}</div>
            <LineViz data={trend} area />
          </div>
          <div>
            <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>{t("HOTSPOTS BY DISTRICT")}</div>
            <BarViz data={hotspots} horizontal color="#ff8a4d" />
          </div>
        </div>
      </Panel>

      {temporal && (
        <div className="grid cols-2">
          <Panel title={t("Seasonal Signature (by month)")}><BarViz data={temporal.by_month} color="#24d18b" /></Panel>
          <Panel title={t("Weekly Signature (by weekday)")}><BarViz data={temporal.by_weekday} color="#2f81f7" /></Panel>
        </div>
      )}

      <Panel title={t("Detected Crime Patterns & Emerging Clusters")}>
        {patterns.length === 0 ? <Loading /> : (
          <div className="grid cols-2">
            {patterns.map((p) => (
              <div key={p.id} className="card" style={{ background: "var(--panel-2)" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <div style={{ fontWeight: 600 }}>{p.name}</div>
                  <Chip kind="accent">{p.case_count} {t("cases")}</Chip>
                </div>
                <div className="faint" style={{ fontSize: 12, margin: "4px 0 8px" }}>
                  {p.crime_type} · {p.district}
                </div>
                <p className="dim" style={{ fontSize: 13, margin: "0 0 8px", lineHeight: 1.5 }}>{p.description}</p>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <Chip kind="amber">{p.temporal}</Chip>
                  {p.mo_tags.split(",").map((tg: string) => <span key={tg} className="chip">{tg.trim()}</span>)}
                </div>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
