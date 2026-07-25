import { useEffect, useState, useCallback } from "react";
import { ArrowLeft, BarChart3, MapPin, Clock, Brain, DollarSign } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { Chip, Loading, Panel, Stat, BarViz, LineViz } from "../components";

export default function CrimeCategoryAnalytics() {
  const { t } = useLang();
  const [crimeTypes, setCrimeTypes] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.byType().then((rows: any[]) => {
      const types = rows.map((r) => r.label).filter(Boolean);
      setCrimeTypes(types);
      if (types.length > 0) setSelected(types[0]);
    });
  }, []);

  const load = useCallback(() => {
    if (!selected) return;
    setLoading(true);
    api.crimeCategory(selected).then((d: any) => { setData(d); setLoading(false); });
  }, [selected]);

  useEffect(() => { load(); }, [load]);

  const inr = (n: number) => "₹" + Intl.NumberFormat("en-IN", { notation: "compact" }).format(n);

  return (
    <div className="grid" style={{ gap: 16 }}>
      {/* Crime type selector */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <BarChart3 size={20} style={{ color: "var(--accent)" }} />
        <h2 style={{ margin: 0, fontSize: 18 }}>{t("Crime Category Analytics")}</h2>
        <select value={selected} onChange={(e) => setSelected(e.target.value)}
          style={{ minWidth: 200, fontSize: 14 }}>
          {crimeTypes.map((ct) => <option key={ct} value={ct}>{ct}</option>)}
        </select>
      </div>

      {loading || !data ? <Loading label={t("Loading…")} /> : data.total === 0 ? (
        <Panel><div className="faint center" style={{ padding: 40 }}>{t("No cases found for this crime type.")}</div></Panel>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid cols-4">
            <Stat label={t("Total Cases")} value={data.total} color="var(--accent)" />
            <Stat label={t("Total Victims")} value={data.demographic.total_victims} />
            <Stat label={t("Financial Cases")} value={data.summary.financial_count}
              sub={data.summary.total_loss > 0 ? inr(data.summary.total_loss) : undefined} />
            <Stat label={t("Avg Loss")} value={data.summary.avg_loss > 0 ? inr(data.summary.avg_loss) : "—"} />
          </div>

          {/* Status + Severity */}
          <div className="grid cols-2">
            <Panel title={t("Case Status Distribution")}>
              {data.summary.by_status.length > 0 ? (
                <BarViz data={data.summary.by_status} height={220} horizontal />
              ) : <div className="faint">{t("No data.")}</div>}
            </Panel>
            <Panel title={t("Severity Distribution")}>
              {data.summary.by_severity.length > 0 ? (
                <BarViz data={data.summary.by_severity} height={220} horizontal color="#e53e3e" />
              ) : <div className="faint">{t("No data.")}</div>}
            </Panel>
          </div>

          {/* Demographic */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
            <h3 style={{ margin: 0 }}>{t("Demographic Analysis")}</h3>
          </div>
          <div className="grid cols-2">
            <Panel title={t("Victim Age Distribution")}>
              {data.demographic.victim_age_bands.some((d: any) => d.value > 0) ? (
                <BarViz data={data.demographic.victim_age_bands} height={220} />
              ) : <div className="faint center" style={{ height: 150 }}>{t("No age data available.")}</div>}
            </Panel>
            <Panel title={t("Victim Gender Distribution")}>
              {data.demographic.victim_gender.length > 0 ? (
                <BarViz data={data.demographic.victim_gender} height={220} color="#9f7aea" />
              ) : <div className="faint center" style={{ height: 150 }}>{t("No gender data available.")}</div>}
            </Panel>
          </div>

          {/* Geographic */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
            <MapPin size={16} />
            <h3 style={{ margin: 0 }}>{t("Geographic Analysis")}</h3>
          </div>
          <div className="grid cols-2">
            <Panel title={t("By District")}>
              {data.geographic.by_district.length > 0 ? (
                <BarViz data={data.geographic.by_district.slice(0, 12)} height={280} horizontal />
              ) : <div className="faint">{t("No data.")}</div>}
            </Panel>
            <Panel title={t("Top Police Stations")}>
              {data.geographic.by_station.length > 0 ? (
                <div style={{ maxHeight: 300, overflowY: "auto" }}>
                  {data.geographic.by_station.map((s: any, i: number) => (
                    <div key={s.label} style={{ display: "flex", justifyContent: "space-between",
                      padding: "6px 8px", borderBottom: "1px solid var(--border)",
                      background: i < 3 ? "var(--panel-2)" : "transparent" }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ width: 20, height: 20, borderRadius: "50%", display: "flex",
                          alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700,
                          background: i < 3 ? "var(--red, #e53e3e)" : "var(--border)",
                          color: i < 3 ? "#fff" : "var(--text)" }}>{i + 1}</span>
                        <span style={{ fontSize: 12 }}>{s.label}</span>
                      </div>
                      <Chip kind={i < 3 ? "red" : "accent"}>{s.value}</Chip>
                    </div>
                  ))}
                </div>
              ) : <div className="faint">{t("No data.")}</div>}
            </Panel>
          </div>

          {/* Temporal */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
            <Clock size={16} />
            <h3 style={{ margin: 0 }}>{t("Temporal Analysis")}</h3>
          </div>
          <Panel title={t("Monthly Crime Trend")}>
            {data.temporal.monthly_trend.length > 0 ? (
              <LineViz data={data.temporal.monthly_trend} height={250} area />
            ) : <div className="faint center" style={{ height: 150 }}>{t("No trend data available.")}</div>}
          </Panel>
          <div className="grid cols-2">
            <Panel title={t("Seasonal Pattern (by Month)")}>
              {data.temporal.by_month.length > 0 ? (
                <BarViz data={data.temporal.by_month} height={220} />
              ) : <div className="faint">{t("No data.")}</div>}
            </Panel>
            <Panel title={t("Day of Week Pattern")}>
              {data.temporal.by_weekday.length > 0 ? (
                <BarViz data={data.temporal.by_weekday} height={220} color="#48bb78" />
              ) : <div className="faint">{t("No data.")}</div>}
            </Panel>
          </div>

          {/* Behavioural */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 8 }}>
            <Brain size={16} />
            <h3 style={{ margin: 0 }}>{t("Behavioural Analysis")}</h3>
          </div>
          <div className="grid cols-2">
            <Panel title={t("Accused Status")}>
              {data.behavioural.accused_status.length > 0 ? (
                <BarViz data={data.behavioural.accused_status} height={220} horizontal color="#ed8936" />
              ) : <div className="faint center" style={{ height: 150 }}>{t("No accused data.")}</div>}
            </Panel>
            <Panel title={t("Modus Operandi Keywords")}>
              {data.behavioural.modus_operandi_keywords.length > 0 ? (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: 8 }}>
                  {data.behavioural.modus_operandi_keywords.map((kw: any) => (
                    <span key={kw.label} style={{
                      padding: "4px 10px", borderRadius: 14, fontSize: 12, fontWeight: 500,
                      border: "1px solid var(--border)", background: "var(--panel-2)",
                      display: "inline-flex", alignItems: "center", gap: 4,
                    }}>
                      {kw.label} <span className="faint">({kw.value})</span>
                    </span>
                  ))}
                </div>
              ) : <div className="faint center" style={{ height: 150 }}>{t("No MO data available.")}</div>}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}
