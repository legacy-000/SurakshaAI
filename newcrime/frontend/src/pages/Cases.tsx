import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Search, Play, PlusCircle, X } from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { Chip, Loading, Panel } from "../components";

const CRIME_TYPES = [
  "Murder", "Theft", "Robbery", "Assault", "Kidnapping", "Cyber Fraud",
  "Domestic Violence", "Drug Trafficking", "Extortion", "Rioting", "Burglary",
  "Chain Snatching", "Vehicle Theft", "Human Trafficking", "UPI Scam", "Bank Fraud", "Fraud",
];
const SEVERITIES = ["Low", "Medium", "High", "Critical"];
const KARNATAKA_DISTRICTS = [
  "Bengaluru Urban", "Bengaluru Rural", "Mysuru", "Mangaluru", "Hubballi-Dharwad",
  "Belagavi", "Kalaburagi", "Ballari", "Davanagere", "Shivamogga", "Tumakuru",
  "Raichur", "Hassan", "Mandya", "Chitradurga", "Udupi", "Chikkamagaluru",
  "Kodagu", "Ramanagara", "Kolar", "Chikkaballapur", "Bagalkot", "Bidar",
  "Yadgir", "Koppal", "Gadag", "Haveri", "Uttara Kannada", "Vijayapura", "Chamarajanagar",
];

export default function Cases() {
  const nav = useNavigate();
  const { user } = useAuth();
  const { t } = useLang();
  const canWork = user?.permissions.screens.includes("work");
  const canInv = user?.permissions.can_investigate;
  const [filters, setFilters] = useState<any>({ crime_types: [], districts: [], statuses: [] });
  const [q, setQ] = useState("");
  const [crime, setCrime] = useState("");
  const [district, setDistrict] = useState("");
  const [status, setStatus] = useState("");
  const [data, setData] = useState<any>(null);
  const [showFIR, setShowFIR] = useState(false);

  const reload = () => api.cases({ q, crime_type: crime, district, status, limit: 60 }).then(setData);

  useEffect(() => { api.caseFilters().then(setFilters); }, []);
  useEffect(() => {
    const tm = setTimeout(reload, 250);
    return () => clearTimeout(tm);
  }, [q, crime, district, status]);

  const inr = (n: number) => n ? "₹" + Intl.NumberFormat("en-IN", { notation: "compact" }).format(n) : "—";

  return (
    <div className="grid" style={{ gap: 16 }}>
      {/* Register FIR button */}
      {canInv && (
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button className="btn primary" onClick={() => setShowFIR(!showFIR)}>
            {showFIR ? <><X size={14} /> {t("Cancel")}</> : <><PlusCircle size={14} /> {t("Register FIR")}</>}
          </button>
        </div>
      )}

      {showFIR && <FIRForm filters={filters} onCreated={(c: any) => { setShowFIR(false); reload(); nav(`/cases/${c.id}`); }} t={t} />}

      <Panel title={t("Search & Filter")}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <div style={{ position: "relative", flex: 1, minWidth: 220 }}>
            <Search size={15} style={{ position: "absolute", left: 10, top: 10, color: "var(--text-faint)" }} />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t("Search FIR no, title, location...")}
              style={{ width: "100%", paddingLeft: 32 }} />
          </div>
          <select value={crime} onChange={(e) => setCrime(e.target.value)}>
            <option value="">{t("All crime types")}</option>
            {filters.crime_types.map((c: string) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={district} onChange={(e) => setDistrict(e.target.value)}>
            <option value="">{t("All districts")}</option>
            {filters.districts.map((d: string) => <option key={d} value={d}>{d}</option>)}
          </select>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">{t("All statuses")}</option>
            {filters.statuses.map((s: string) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </Panel>

      <Panel title={data ? `${t("Cases")} (${data.total})` : t("Cases")}>
        {!data ? <Loading /> : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>{t("FIR No.")}</th>
                  <th>{t("Title")}</th>
                  <th>{t("Crime Type")}</th>
                  <th>{t("District")}</th>
                  <th>{t("Severity")}</th>
                  <th>{t("Status")}</th>
                  <th>{t("Loss")}</th>
                  {canWork && <th>{t("Work a Case")}</th>}
                </tr>
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
                        <Play size={11} /> {t("Start")}
                      </button>
                    </td>}
                  </tr>
                ))}
              </tbody>
            </table>
            {data.items.length === 0 && <div className="faint center" style={{ padding: 30 }}>{t("No cases match.")}</div>}
          </div>
        )}
      </Panel>
    </div>
  );
}

function FIRForm({ filters, onCreated, t }: { filters: any; onCreated: (c: any) => void; t: (s: string) => string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    title: "", description: "", crime_type: "", severity: "Medium",
    district: "", station: "", location_name: "", modus_operandi: "",
    fir_number: "", occurrence_date: "", is_financial: false, loss_amount: "",
  });

  const set = (k: string, v: any) => setForm((p) => ({ ...p, [k]: v }));

  const submit = async () => {
    if (!form.title.trim()) { setError(t("Title is required")); return; }
    if (!form.crime_type) { setError(t("Crime type is required")); return; }
    if (!form.district) { setError(t("District is required")); return; }
    setError(""); setBusy(true);
    try {
      const res = await api.createFIR({
        ...form,
        is_financial: form.is_financial ? "true" : "false",
        loss_amount: form.loss_amount || "0",
      });
      if (res.ok) {
        onCreated(res.case);
      } else {
        setError(res.detail || "Failed to create FIR");
      }
    } catch (e: any) {
      setError(e.message || "Error");
    } finally { setBusy(false); }
  };

  return (
    <Panel title={t("Register New FIR")}>
      <div className="grid" style={{ gap: 12 }}>
        {error && <div style={{ color: "var(--red, #e53e3e)", fontSize: 13, padding: "6px 10px", border: "1px solid var(--red, #e53e3e)", borderRadius: 6 }}>{error}</div>}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("FIR Number")} ({t("auto-generated if blank")})</label>
            <input placeholder="FIR/2026/BLR/1001" value={form.fir_number} onChange={(e) => set("fir_number", e.target.value)} style={{ width: "100%" }} />
          </div>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Title")} *</label>
            <input placeholder={t("Brief description of incident")} value={form.title} onChange={(e) => set("title", e.target.value)} style={{ width: "100%" }} />
          </div>
        </div>

        <div>
          <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Description")}</label>
          <textarea placeholder={t("Detailed incident description...")} value={form.description} onChange={(e) => set("description", e.target.value)} rows={3} style={{ width: "100%" }} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Crime Type")} *</label>
            <select value={form.crime_type} onChange={(e) => set("crime_type", e.target.value)} style={{ width: "100%" }}>
              <option value="">{t("Select...")}</option>
              {CRIME_TYPES.map((ct) => <option key={ct} value={ct}>{ct}</option>)}
            </select>
          </div>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Severity")}</label>
            <select value={form.severity} onChange={(e) => set("severity", e.target.value)} style={{ width: "100%" }}>
              {SEVERITIES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Date of Occurrence")}</label>
            <input type="datetime-local" value={form.occurrence_date} onChange={(e) => set("occurrence_date", e.target.value)} style={{ width: "100%" }} />
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("District")} *</label>
            <select value={form.district} onChange={(e) => set("district", e.target.value)} style={{ width: "100%" }}>
              <option value="">{t("Select...")}</option>
              {KARNATAKA_DISTRICTS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Police Station")}</label>
            <input placeholder={t("Station name")} value={form.station} onChange={(e) => set("station", e.target.value)} style={{ width: "100%" }} />
          </div>
          <div>
            <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Location")}</label>
            <input placeholder={t("Place of incident")} value={form.location_name} onChange={(e) => set("location_name", e.target.value)} style={{ width: "100%" }} />
          </div>
        </div>

        <div>
          <label className="faint" style={{ fontSize: 11, display: "block", marginBottom: 4 }}>{t("Modus Operandi")}</label>
          <textarea placeholder={t("How the crime was committed...")} value={form.modus_operandi} onChange={(e) => set("modus_operandi", e.target.value)} rows={2} style={{ width: "100%" }} />
        </div>

        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: 13 }}>
            <input type="checkbox" checked={form.is_financial} onChange={(e) => set("is_financial", e.target.checked)} />
            {t("Financial crime")}
          </label>
          {form.is_financial && (
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span className="faint" style={{ fontSize: 12 }}>{t("Loss Amount")} (INR):</span>
              <input type="number" placeholder="0" value={form.loss_amount} onChange={(e) => set("loss_amount", e.target.value)}
                style={{ width: 140 }} />
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", paddingTop: 8 }}>
          <button className="btn primary" onClick={submit} disabled={busy}>
            {busy ? t("Registering...") : t("Register FIR")}
          </button>
        </div>
      </div>
    </Panel>
  );
}
