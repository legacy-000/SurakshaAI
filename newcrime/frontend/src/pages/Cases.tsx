import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Play } from "lucide-react";
import { api } from "../api";
import { useAuth } from "../context";
import { Chip, Loading, Panel } from "../components";

export default function Cases() {
  const nav = useNavigate();
  const { user } = useAuth();
  const canWork = user?.permissions.screens.includes("work");
  const [filters, setFilters] = useState<any>({ crime_types: [], districts: [], statuses: [] });
  const [q, setQ] = useState("");
  const [crime, setCrime] = useState("");
  const [district, setDistrict] = useState("");
  const [status, setStatus] = useState("");
  const [data, setData] = useState<any>(null);

  useEffect(() => { api.caseFilters().then(setFilters); }, []);
  useEffect(() => {
    const t = setTimeout(() => {
      api.cases({ q, crime_type: crime, district, status, limit: 60 }).then(setData);
    }, 250);
    return () => clearTimeout(t);
  }, [q, crime, district, status]);

  const inr = (n: number) => n ? "₹" + Intl.NumberFormat("en-IN", { notation: "compact" }).format(n) : "—";

  return (
    <div className="grid" style={{ gap: 16 }}>
      <Panel title="Search & Filter">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <div style={{ position: "relative", flex: 1, minWidth: 220 }}>
            <Search size={15} style={{ position: "absolute", left: 10, top: 10, color: "var(--text-faint)" }} />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search FIR no, title, location…"
              style={{ width: "100%", paddingLeft: 32 }} />
          </div>
          <select value={crime} onChange={(e) => setCrime(e.target.value)}>
            <option value="">All crime types</option>
            {filters.crime_types.map((c: string) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={district} onChange={(e) => setDistrict(e.target.value)}>
            <option value="">All districts</option>
            {filters.districts.map((d: string) => <option key={d} value={d}>{d}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {filters.statuses.map((s: string) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </Panel>

      <Panel title={data ? `Cases (${data.total})` : "Cases"}>
        {!data ? <Loading /> : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr><th>FIR No.</th><th>Title</th><th>Crime Type</th><th>District</th>
                  <th>Severity</th><th>Status</th><th>Loss</th>{canWork && <th>Work a Case</th>}</tr>
              </thead>
              <tbody>
                {data.items.map((c: any) => (
                  <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => nav(`/cases/${c.id}`)}>
                    <td className="mono" style={{ fontSize: 12 }}>{c.fir_number}</td>
                    <td>{c.title}</td>
                    <td>{c.crime_type}</td>
                    <td className="dim">{c.district}</td>
                    <td><Chip kind={c.severity}>{c.severity}</Chip></td>
                    <td><Chip>{c.status}</Chip></td>
                    <td className="dim">{inr(c.loss_amount)}</td>
                    {canWork && <td onClick={(e) => { e.stopPropagation(); nav(`/cases/${c.id}`); }}>
                      <button className="btn primary" style={{ padding: "4px 9px", fontSize: 11 }}>
                        <Play size={11} /> Start
                      </button>
                    </td>}
                  </tr>
                ))}
              </tbody>
            </table>
            {data.items.length === 0 && <div className="faint center" style={{ padding: 30 }}>No cases match.</div>}
          </div>
        )}
      </Panel>
    </div>
  );
}
