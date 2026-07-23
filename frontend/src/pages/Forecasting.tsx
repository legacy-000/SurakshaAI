import { useEffect, useState } from "react";
import { TrendingUp, AlertTriangle } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { Chip, Loading, Panel, Stat } from "../components";

export default function Forecasting() {
  const { t } = useLang();
  const [preds, setPreds] = useState<any[] | null>(null);
  const [risk, setRisk] = useState("");

  useEffect(() => { setPreds(null); api.predictions(risk).then(setPreds); }, [risk]);

  if (!preds) return <Loading label={t("Loading forecasts…")} />;
  const critical = preds.filter((p) => p.risk_level === "Critical").length;
  const high = preds.filter((p) => p.risk_level === "High").length;

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid cols-3">
        <Stat label={t("Active Forecasts")} value={preds.length} />
        <Stat label={t("Critical-risk windows")} value={critical} color="#ff4d5e" />
        <Stat label={t("High-risk windows")} value={high} color="#ffb020" />
      </div>

      <Panel title={<span><TrendingUp size={13} /> {t("Predicted Crime Risk — Early Warning")}</span> as any}
        right={
          <select value={risk} onChange={(e) => setRisk(e.target.value)}>
            <option value="">{t("All levels")}</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
          </select>
        }>
        <div className="grid cols-2">
          {preds.map((p) => (
            <div key={p.id} className="card" style={{ background: "var(--panel-2)", borderLeft: `3px solid ${
              p.risk_level === "Critical" ? "var(--red)" : p.risk_level === "High" ? "var(--amber)" : "var(--accent)"}` }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{p.crime_type}</div>
                  <div className="faint" style={{ fontSize: 12 }}>{p.target_area}</div>
                </div>
                <Chip kind={p.risk_level}>{p.risk_level}</Chip>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "12px 0" }}>
                <div className="bar" style={{ flex: 1 }}><span style={{ width: `${p.probability * 100}%` }} /></div>
                <b style={{ fontSize: 18 }}>{Math.round(p.probability * 100)}%</b>
              </div>
              <div className="faint" style={{ fontSize: 12 }}>
                {t("Window:")} {p.window_start?.slice(0, 10)} → {p.window_end?.slice(0, 10)}
              </div>
              <div style={{ marginTop: 8, display: "flex", gap: 6, alignItems: "start" }}>
                <AlertTriangle size={13} className="dim" style={{ marginTop: 2, flexShrink: 0 }} />
                <div className="dim" style={{ fontSize: 12, lineHeight: 1.5 }}>{p.contributing_factors}</div>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
