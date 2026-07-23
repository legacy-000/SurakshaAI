import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Play, Briefcase } from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { Chip, Loading, Panel, Stat } from "../components";

const ACTIVE = ["Open", "Under Investigation"];

export default function WorkCase() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { t } = useLang();
  const [data, setData] = useState<any>(null);
  const [q, setQ] = useState("");
  const [filters, setFilters] = useState<any>({ crime_types: [], districts: [], statuses: [] });
  const [crime, setCrime] = useState("");

  useEffect(() => { api.caseFilters().then(setFilters); }, []);
  useEffect(() => {
    const tm = setTimeout(() => api.cases({ q, crime_type: crime, limit: 80 }).then(setData), 200);
    return () => clearTimeout(tm);
  }, [q, crime]);

  const items = data ? [...data.items].sort((a: any, b: any) =>
    (ACTIVE.includes(b.status) ? 1 : 0) - (ACTIVE.includes(a.status) ? 1 : 0)) : [];
  const active = items.filter((c: any) => ACTIVE.includes(c.status)).length;

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid cols-3">
        <Stat label={t("Cases in worklist")} value={data ? data.total : "…"} />
        <Stat label={t("Awaiting action")} value={active} color="#ffb020" />
        <Stat label={t("Your scope")} value={<span style={{ textTransform: "capitalize" }}>{user?.permissions.scope}</span>} color="#2f81f7" />
      </div>

      <Panel title={<span><Briefcase size={13} /> {t("Work a Case — Investigation Worklist")}</span> as any}
        info={{ what: "Pick a case to open its Investigation Dashboard — stages, evidence, witnesses, notes and AI.", data: "cases (role-scoped)", brief: "Work a Case (#3)" }}
        right={
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ position: "relative" }}>
              <Search size={14} style={{ position: "absolute", left: 9, top: 10, color: "var(--text-faint)" }} />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("Search FIR / title…")} style={{ paddingLeft: 30 }} />
            </div>
            <select value={crime} onChange={(e) => setCrime(e.target.value)}>
              <option value="">{t("All crime types")}</option>
              {filters.crime_types.map((c: string) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        }>
        {!data ? <Loading /> : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr><th>{t("FIR No.")}</th><th>{t("Title")}</th><th>{t("Crime Type")}</th><th>{t("District")}</th>
                  <th>{t("Severity")}</th><th>{t("Status")}</th><th>{t("Work a Case")}</th></tr>
              </thead>
              <tbody>
                {items.map((c: any) => (
                  <tr key={c.id}>
                    <td className="mono" style={{ fontSize: 12 }}>{c.fir_number}</td>
                    <td>{c.title}</td>
                    <td>{c.crime_type}</td>
                    <td className="dim">{c.district}</td>
                    <td><Chip kind={c.severity}>{c.severity}</Chip></td>
                    <td><Chip>{c.status}</Chip></td>
                    <td>
                      <button className="btn primary" style={{ padding: "5px 10px", fontSize: 12 }}
                        onClick={() => nav(`/cases/${c.id}`)}>
                        <Play size={12} /> {t("Start Investigation")}
                      </button>
                    </td>
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
