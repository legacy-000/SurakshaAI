import { useEffect, useState } from "react";
import { api } from "../api";
import { useLang } from "../context";
import { BarViz, Chip, DonutViz, Legend, Loading, Panel } from "../components";

export default function Socio() {
  const { t } = useLang();
  const [d, setD] = useState<any>({});

  useEffect(() => {
    Promise.all([
      api.socioGender(), api.socioAge(), api.socioSes(), api.socioEdu(),
      api.socioUrbanRural(), api.riskFactors(), api.crimeByDemographic(),
    ]).then(([gender, age, ses, edu, ur, risk, byDemo]) =>
      setD({ gender, age, ses, edu, ur, risk, byDemo }));
  }, []);

  if (!d.gender) return <Loading label={t("Loading sociological insights…")} />;

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid cols-3">
        <Panel title={t("Offender Age Bands")}><BarViz data={d.age} color="#2f81f7" /></Panel>
        <Panel title={t("Gender Split")}>
          <DonutViz data={d.gender} height={190} /><Legend data={d.gender} />
        </Panel>
        <Panel title={t("Urban vs Rural")}>
          <DonutViz data={d.ur} height={190} /><Legend data={d.ur} />
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title={t("Socio-economic Background")}><BarViz data={d.ses} color="#a06bff" /></Panel>
        <Panel title={t("Education Level")}><BarViz data={d.edu} color="#24d18b" /></Panel>
      </div>

      <Panel title={t("Social Risk Factors (correlation with offender risk)")}>
        <div className="dim" style={{ fontSize: 12, marginBottom: 10 }}>
          Baseline average offender risk: <b>{d.risk.baseline_avg_risk}</b>. Bars above baseline
          indicate elevated risk for that social indicator.
        </div>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead><tr><th>{t("Social factor")}</th><th>{t("Share of offenders")}</th><th>{t("Avg. risk score")}</th><th>{t("vs baseline")}</th></tr></thead>
            <tbody>
              {d.risk.factors.map((f: any) => {
                const delta = +(f.avg_risk - d.risk.baseline_avg_risk).toFixed(1);
                return (
                  <tr key={f.factor}>
                    <td>{f.factor}</td>
                    <td className="dim">{f.share}%</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div className="bar" style={{ width: 80 }}><span style={{ width: `${f.avg_risk}%` }} /></div>
                        {f.avg_risk}
                      </div>
                    </td>
                    <td><Chip kind={delta > 0 ? "Critical" : "Low"}>{delta > 0 ? "+" : ""}{delta}</Chip></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title={t("Dominant Crime Type by Socio-economic Band")}>
        <div className="grid cols-3">
          {d.byDemo.map((row: any) => (
            <div key={row.socio_economic} className="card" style={{ background: "var(--panel-2)" }}>
              <div className="panel-title" style={{ marginBottom: 8 }}>{row.socio_economic}</div>
              {row.top_crimes.map((c: any) => (
                <div key={c.crime} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "3px 0" }}>
                  <span>{c.crime}</span><span className="dim">{c.count}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
