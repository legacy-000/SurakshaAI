import { useEffect, useMemo, useState } from "react";
import { useLang } from "../context";
import { api } from "../api";
import { KarnatakaMap } from "../KarnatakaMap";
import { Panel, Stat, Loading, BarViz, LineViz } from "../components";

interface DistrictRow {
  district: string; count: number; lat: number; lon: number;
  loss?: number; top_crime?: string;
}

export default function HotspotDashboard() {
  const { t } = useLang();
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState("");
  const [crimeType, setCrimeType] = useState("");
  const [status, setStatus] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setErr("");
    api.hotspotDashboard({ crime_type: crimeType, status })
      .then(setData)
      // this previously swallowed every failure and left a bare page title
      .catch((e: any) => setErr(e?.message || "Could not load hotspot data."));
  }, [crimeType, status]);

  const districts: DistrictRow[] = useMemo(
    () => (Array.isArray(data?.state_view) ? data.state_view : []), [data]);

  const trend = useMemo(
    () => (data?.crime_trend || []).map((p: any) => ({ label: p.month, value: p.count })),
    [data]);

  const ranked = useMemo(
    () => [...districts].sort((a, b) => b.count - a.count), [districts]);

  const totalLoss = useMemo(
    () => districts.reduce((s, d) => s + (d.loss || 0), 0), [districts]);

  const sel = selected ? districts.find((d) => d.district === selected) : null;

  return (
    <div style={{ display: "grid", gap: 16 }}>
      <h2 style={{ fontSize: 22, fontWeight: 700 }}>{t("Crime Hotspot Dashboard")}</h2>

      {err && (
        <div style={{ padding: "10px 14px", fontSize: 13,
          border: "1px solid rgba(255,77,94,0.35)", background: "rgba(255,77,94,0.08)" }}>
          {err}
        </div>
      )}

      {!data && !err && <Loading label={t("Loading hotspot data…")} />}

      {data && (
        <>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <select value={crimeType} onChange={(e) => setCrimeType(e.target.value)}>
              <option value="">{t("All crime types")}</option>
              {(data.filter_options?.crime_types || []).map((c: string) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">{t("All statuses")}</option>
              {(data.filter_options?.statuses || []).map((s: string) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            {(crimeType || status) && (
              <button className="btn ghost" style={{ fontSize: 12 }}
                onClick={() => { setCrimeType(""); setStatus(""); }}>
                {t("Clear filters")}
              </button>
            )}
          </div>

          <div style={{ display: "grid", gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
            <Stat label={t("Total cases")} value={data.total_crimes ?? 0} />
            <Stat label={t("Districts affected")} value={districts.length} color="#a06bff" />
            <Stat label={t("Top hotspot")} value={ranked[0]?.district || "—"}
              sub={ranked[0] ? `${ranked[0].count} ${t("cases")}` : ""} color="#ff4d5e" />
            <Stat label={t("Reported loss")}
              value={`₹${(totalLoss / 10000000).toFixed(2)} Cr`} color="#ffb020" />
          </div>

          <Panel title={t("Where crime is concentrated")}>
            {districts.length === 0 ? (
              <div className="faint" style={{ fontSize: 13 }}>
                {t("No cases match these filters.")}
              </div>
            ) : (
              <KarnatakaMap districts={districts} selected={selected}
                onSelect={setSelected} height={440} />
            )}
          </Panel>

          {sel && (
            <Panel title={`${sel.district} — ${t("district detail")}`}>
              <div style={{ display: "grid", gap: 12,
                gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" }}>
                <Stat label={t("Cases")} value={sel.count} />
                <Stat label={t("Top crime")} value={sel.top_crime || "—"} color="#a06bff" />
                <Stat label={t("Reported loss")}
                  value={`₹${((sel.loss || 0) / 100000).toFixed(1)} L`} color="#ffb020" />
              </div>
            </Panel>
          )}

          <div style={{ display: "grid", gap: 12,
            gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))" }}>
            <Panel title={t("Cases by district")}>
              {ranked.length ? (
                <BarViz horizontal height={Math.max(220, ranked.length * 24)}
                  data={ranked.map((d) => ({ label: d.district, value: d.count }))} />
              ) : (
                <div className="faint" style={{ fontSize: 13 }}>{t("No data.")}</div>
              )}
            </Panel>
            <Panel title={t("Trend over time")}>
              {trend.length ? (
                <LineViz data={trend} height={260} area />
              ) : (
                <div className="faint" style={{ fontSize: 13 }}>{t("No trend data.")}</div>
              )}
            </Panel>
          </div>
        </>
      )}
    </div>
  );
}
