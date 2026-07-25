import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useLang } from "../context";
import { Chip, DonutViz, Legend, Loading, Panel } from "../components";

const BAND_KIND: Record<string, string> = { Low: "Low", Medium: "Medium", High: "High", Critical: "Critical" };

export default function Profiling() {
  const nav = useNavigate();
  const { t } = useLang();
  const [dist, setDist] = useState<any[]>([]);
  const [band, setBand] = useState("");
  const [habitual, setHabitual] = useState(false);
  const [rows, setRows] = useState<any[] | null>(null);

  useEffect(() => { api.riskDistribution().then(setDist); }, []);
  useEffect(() => {
    setRows(null);
    api.offenders({ band, habitual: habitual ? true : undefined, limit: 60 }).then(setRows);
  }, [band, habitual]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid cols-3">
        <Panel title={t("Risk-band Distribution")}>
          <DonutViz data={dist} height={190} />
          <Legend data={dist} />
        </Panel>
        <Panel title={t("Filters")} className="">
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div>
              <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>{t("Risk band")}</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {["", "Critical", "High", "Medium", "Low"].map((b) => (
                  <button key={b} className={`chip ${band === b ? "accent" : ""}`} style={{ cursor: "pointer" }}
                    onClick={() => setBand(b)}>{b || t("All")}</button>
                ))}
              </div>
            </div>
            <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 13, cursor: "pointer" }}>
              <input type="checkbox" checked={habitual} onChange={(e) => setHabitual(e.target.checked)}
                style={{ width: 16, height: 16 }} />
              {t("Habitual / repeat offenders only")}
            </label>
          </div>
          <div className="dim" style={{ fontSize: 12, marginTop: 14, lineHeight: 1.6 }}>
            Risk score combines prior convictions, linked cases, absconding status and behavioural
            signals. Higher scores are prioritised for investigation.
          </div>
        </Panel>
        <Panel title={t("Top Propensity Tags")}>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {rows && [...new Set(rows.flatMap((r) => (r.propensity || "").split(",").map((s: string) => s.trim())).filter(Boolean))]
              .slice(0, 14).map((tg) => <span key={tg} className="chip">{tg}</span>)}
          </div>
        </Panel>
      </div>

      <Panel title={rows ? `${t("Offenders")} (${rows.length})` : t("Offenders")}>
        {!rows ? <Loading /> : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead><tr><th>{t("Name")}</th><th>{t("Age/Gender")}</th><th>{t("District")}</th><th>{t("Priors")}</th>
                <th>{t("Cases")}</th><th>{t("Risk")}</th><th>{t("Band")}</th><th>{t("Modus Operandi")}</th></tr></thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} style={{ cursor: "pointer" }} onClick={() => nav(`/offender/${r.id}`)}>
                    <td>{r.name} {r.habitual && <Chip kind="amber">habitual</Chip>}</td>
                    <td className="dim">{r.age}/{r.gender}</td>
                    <td className="dim">{r.district}</td>
                    <td>{r.priors}</td>
                    <td>{r.cases}</td>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div className="bar" style={{ width: 60 }}><span style={{ width: `${r.risk_score}%` }} /></div>
                        {r.risk_score}
                      </div>
                    </td>
                    <td><Chip kind={BAND_KIND[r.risk_band]}>{r.risk_band}</Chip></td>
                    <td className="dim" style={{ fontSize: 12 }}>{r.modus_operandi}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </div>
  );
}
