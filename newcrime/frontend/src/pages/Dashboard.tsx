import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { api } from "../api";
import { BarViz, DonutViz, Legend, LineViz, Loading, Panel, Stat, Chip } from "../components";

export default function Dashboard() {
  const nav = useNavigate();
  const [ov, setOv] = useState<any>(null);
  const [byType, setByType] = useState<any[]>([]);
  const [byHead, setByHead] = useState<any[]>([]);
  const [trend, setTrend] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    api.overview().then(setOv);
    api.byType().then((d) => setByType(d.slice(0, 8)));
    api.byHead().then(setByHead);
    api.trend().then(setTrend);
    api.alerts(true).then((a) => setAlerts(a.slice(0, 5)));
  }, []);

  if (!ov) return <Loading label="Loading command dashboard…" />;
  const inr = (n: number) => "₹" + Intl.NumberFormat("en-IN", { notation: "compact" }).format(n);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid cols-4">
        <Stat label="Total Cases" value={ov.total_cases} sub={`${ov.open_cases} open`} />
        <Stat label="Clearance Rate" value={`${ov.clearance_rate}%`} sub={`${ov.solved_cases} solved`} color="#24d18b" />
        <Stat label="High-risk Offenders" value={ov.high_risk_offenders} sub={`of ${ov.total_accused} accused`} color="#ff4d5e" />
        <Stat label="Reported Loss" value={inr(ov.total_loss)} sub={`${ov.active_alerts} active alerts`} color="#ffb020" />
      </div>

      <div className="grid cols-3">
        <Panel title="Crime Trend (monthly)" className="" >
          <LineViz data={trend} area color="#00d1ff" />
        </Panel>
        <Panel title="Top Crime Types">
          <BarViz data={byType} horizontal color="#2f81f7" />
        </Panel>
        <Panel title="By Crime Head">
          <DonutViz data={byHead} height={200} />
          <Legend data={byHead} />
        </Panel>
      </div>

      <Panel title="Active Alerts & Early Warnings"
        right={<button className="btn ghost" onClick={() => nav("/alerts")}>View all <ArrowRight size={14} /></button>}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {alerts.length === 0 && <div className="faint">No active alerts.</div>}
          {alerts.map((a) => (
            <div key={a.id} style={{ display: "flex", alignItems: "center", gap: 12,
              padding: "10px 12px", border: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <AlertTriangle size={16} className="dim" />
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600 }}>{a.title}</div>
                <div className="faint" style={{ fontSize: 12 }}>{a.district} · {a.alert_type}</div>
              </div>
              <Chip kind={a.severity}>{a.severity}</Chip>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
