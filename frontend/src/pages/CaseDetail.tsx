import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, MapPin, User, Clock, Users, GitCompare, FileDown, Upload,
  Pin, Trash2, Check, ChevronRight, Sparkles, ShieldCheck, FileText, UserPlus,
} from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { caseBriefing } from "../briefing";
import { Chip, Loading, Panel } from "../components";

const TABS = ["Overview", "Evidence", "Witnesses", "Notes", "Timeline", "AI Assistant", "Similar Cases"];

export default function CaseDetail() {
  const { id } = useParams();
  const cid = Number(id);
  const nav = useNavigate();
  const { user } = useAuth();
  const { t } = useLang();
  const [c, setC] = useState<any>(null);
  const [similar, setSimilar] = useState<any>(null);
  const [bundle, setBundle] = useState<any>(null);
  const [tab, setTab] = useState("Overview");

  const canInv = user?.permissions.can_investigate;
  const [exporting, setExporting] = useState(false);

  const exportBriefing = async () => {
    setExporting(true);
    try {
      const [notes, witnesses, evidence] = await Promise.all([
        api.notes(cid), api.witnesses(cid), api.evidence(cid),
      ]);
      caseBriefing(c, similar, { bundle, notes, witnesses, evidence },
        { full_name: user!.full_name, rank: user!.rank, badge_number: user!.badge_number });
    } finally { setExporting(false); }
  };

  const loadBundle = () => api.investigation(cid).then(setBundle);
  useEffect(() => {
    api.caseDetail(cid).then(setC);
    api.similarCases(cid).then(setSimilar);
    loadBundle();
  }, [id]);

  if (!c || !bundle) return <Loading label={t("Loading investigation dashboard…")} />;
  const inr = (n: number) => n ? "₹" + Intl.NumberFormat("en-IN").format(n) : "—";

  const tabCount: Record<string, number> = {
    Evidence: bundle.counts.evidence, Witnesses: bundle.counts.witnesses, Notes: bundle.counts.notes,
  };

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
        <button className="btn ghost" style={{ width: "fit-content" }} onClick={() => nav("/cases")}>
          <ArrowLeft size={15} /> {t("Back")}
        </button>
        {user?.permissions.can_export &&
          <button className="btn" onClick={exportBriefing} disabled={exporting}>
            <FileDown size={15} /> {exporting ? t("Preparing…") : t("Generate case briefing (PDF)")}
          </button>}
      </div>

      {/* Case header */}
      <Panel>
        <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
          <div>
            <div className="faint mono" style={{ fontSize: 12 }}>{c.fir_number}</div>
            <h2 style={{ margin: "4px 0" }}>{c.title}</h2>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 6 }}>
              <Chip kind="accent">{c.crime_type}</Chip>
              <Chip kind={c.severity}>{c.severity}</Chip>
              <Chip>{c.status}</Chip>
              {c.is_financial && <Chip kind="amber">Financial · {inr(c.loss_amount)}</Chip>}
              {c.pii_masked && <Chip>PII masked</Chip>}
            </div>
          </div>
          <div className="dim" style={{ textAlign: "right", fontSize: 13 }}>
            <div><MapPin size={13} /> {c.location_name}</div>
            <div className="faint" style={{ marginTop: 4 }}>{c.district} · {c.station}</div>
            <div className="faint">{c.occurrence_date?.slice(0, 10)}</div>
          </div>
        </div>
      </Panel>

      {/* Stage tracker */}
      <StageTracker bundle={bundle} canInv={canInv} onChange={loadBundle} t={t} />

      {/* Tabs */}
      <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--border)", flexWrap: "wrap" }}>
        {TABS.map((tb) => (
          <button key={tb} onClick={() => setTab(tb)}
            className="nav-item"
            style={{ width: "auto", borderLeft: "none",
              borderBottom: tab === tb ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === tb ? "var(--accent)" : "var(--text-dim)" }}>
            {t(tb)}{tabCount[tb] != null && <span className="faint"> ({tabCount[tb]})</span>}
          </button>
        ))}
      </div>

      {tab === "Overview" && <Overview c={c} inr={inr} nav={nav} t={t} />}
      {tab === "Evidence" && <EvidenceTab cid={cid} canInv={canInv} categories={bundle.evidence_categories} onChange={loadBundle} t={t} />}
      {tab === "Witnesses" && <WitnessTab cid={cid} canInv={canInv} onChange={loadBundle} t={t} />}
      {tab === "Notes" && <NotesTab cid={cid} onChange={loadBundle} t={t} />}
      {tab === "Timeline" && <TimelineTab c={c} t={t} />}
      {tab === "AI Assistant" && <AITab c={c} t={t} />}
      {tab === "Similar Cases" && <SimilarTab similar={similar} nav={nav} t={t} />}
    </div>
  );
}

/* ── Stage tracker ─────────────────────────────────────────────────── */
function StageTracker({ bundle, canInv, onChange, t }: any) {
  const [busy, setBusy] = useState(false);
  const stages: string[] = bundle.stages;
  const idx = bundle.stage_index;

  const advance = async (stage: string) => {
    setBusy(true);
    try { await api.setStage(bundle.case_id, stage); await onChange(); }
    finally { setBusy(false); }
  };

  return (
    <Panel title={t("Investigation Progress")}
      right={<span className="faint" style={{ fontSize: 12 }}>{bundle.progress}% · {bundle.remaining_stages} {t("stage(s) remaining")}</span>}>
      <div className="bar" style={{ marginBottom: 14 }}><span style={{ width: `${bundle.progress}%` }} /></div>
      <div style={{ display: "flex", gap: 6, overflowX: "auto", paddingBottom: 6 }}>
        {stages.map((s: string, i: number) => {
          const done = i < idx, current = i === idx;
          return (
            <div key={s} style={{ display: "flex", alignItems: "center", gap: 6, flexShrink: 0 }}>
              <div title={s} style={{
                padding: "6px 10px", fontSize: 11, whiteSpace: "nowrap",
                border: `1px solid ${current ? "var(--accent)" : done ? "var(--green)" : "var(--border)"}`,
                color: current ? "var(--accent)" : done ? "var(--green)" : "var(--text-faint)",
                background: current ? "rgba(0,209,255,0.08)" : "var(--panel-2)",
                fontWeight: current ? 700 : 400 }}>
                {done && <Check size={11} style={{ marginRight: 4 }} />}{s}
              </div>
              {i < stages.length - 1 && <ChevronRight size={12} className="faint" />}
            </div>
          );
        })}
      </div>
      {canInv ? (
        <div style={{ display: "flex", gap: 8, marginTop: 14, alignItems: "center", flexWrap: "wrap" }}>
          {idx < stages.length - 1 &&
            <button className="btn primary" disabled={busy} onClick={() => advance(stages[idx + 1])}>
              Advance to "{stages[idx + 1]}" <ChevronRight size={14} />
            </button>}
          <span className="faint" style={{ fontSize: 12 }}>{t("or override:")}</span>
          <select disabled={busy} value={bundle.current_stage}
            onChange={(e) => advance(e.target.value)}>
            {stages.map((s: string) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      ) : <div className="faint" style={{ fontSize: 12, marginTop: 10 }}>{t("Your role can view progress but not change stages.")}</div>}
    </Panel>
  );
}

/* ── Overview ──────────────────────────────────────────────────────── */
function Overview({ c, inr, nav, t }: any) {
  return (
    <div className="grid" style={{ gap: 16 }}>
      <Panel title={t("Case Summary")}
        info={{ what: "FIR narrative, modus operandi and assigned officer.", data: "cases + investigations" }}>
        <p className="dim" style={{ lineHeight: 1.6, marginTop: 0 }}>{c.description}</p>
        <div className="faint" style={{ fontSize: 13 }}>{t("Modus Operandi")}: {c.modus_operandi}</div>
        {c.investigation && (
          <div style={{ marginTop: 12, display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center" }}>
            <div>{t("Officer")}: <b>{c.investigation.officer}</b></div>
            <Chip kind="accent">{c.investigation.status}</Chip>
            <div className="faint" style={{ fontSize: 13 }}>Leads: {c.investigation.leads}</div>
          </div>
        )}
      </Panel>
      <div className="grid cols-2">
        <Panel title={<span><Users size={13} /> {t("Suspects / Accused")}</span> as any}>
          {c.accused.length === 0 ? <div className="faint">{t("None recorded.")}</div> :
            c.accused.map((a: any) => (
              <div key={a.id} style={{ display: "flex", justifyContent: "space-between",
                padding: "8px 0", borderBottom: "1px solid var(--border)", cursor: "pointer" }}
                onClick={() => nav(`/offender/${a.id}`)}>
                <span><User size={13} /> {a.name}</span>
                <span><Chip>{a.role}</Chip> <Chip kind="amber">{a.status}</Chip></span>
              </div>
            ))}
        </Panel>
        <Panel title={t("Victims")}>
          {c.victims.length === 0 ? <div className="faint">{t("None recorded.")}</div> :
            c.victims.map((v: any) => (
              <div key={v.id} style={{ padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                {v.name} <span className="faint">· {v.age}/{v.gender}</span>
              </div>
            ))}
        </Panel>
      </div>
    </div>
  );
}

/* ── Evidence ──────────────────────────────────────────────────────── */
function EvidenceTab({ cid, canInv, categories, onChange, t }: any) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [category, setCategory] = useState("Evidence");
  const [busy, setBusy] = useState(false);
  const load = () => { api.evidence(cid).then(setRows); };
  useEffect(() => { load(); }, [cid]);

  const upload = async (e: any) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try { await api.uploadEvidence(cid, category, file); await load(); await onChange(); }
    finally { setBusy(false); e.target.value = ""; }
  };
  const remove = async (docId: number) => { await api.deleteEvidence(docId); await load(); await onChange(); };
  const kb = (n: number) => n > 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;

  return (
    <Panel title={t("Evidence & Documents")}
      info={{ what: "Upload, categorise and preview case documents. Each gets an AI summary.", data: "evidence_documents", brief: "Evidence management (#6)" }}
      right={canInv &&
        <div style={{ display: "flex", gap: 8 }}>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            {categories.map((c: string) => <option key={c} value={c}>{c}</option>)}
          </select>
          <label className="btn primary" style={{ cursor: "pointer" }}>
            <Upload size={14} /> {busy ? t("Uploading…") : t("Upload")}
            <input type="file" hidden onChange={upload} disabled={busy} />
          </label>
        </div>}>
      {!rows ? <Loading /> : rows.length === 0 ? <div className="faint center" style={{ padding: 24 }}>{t("No evidence uploaded yet.")}</div> : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {rows.map((e) => (
            <div key={e.id} style={{ display: "flex", gap: 12, alignItems: "start", padding: "10px 12px",
              border: "1px solid var(--border)", background: "var(--panel-2)" }}>
              <FileText size={18} className="dim" style={{ marginTop: 2 }} />
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <b>{e.original_name}</b><Chip kind="accent">{e.category}</Chip>
                  <span className="faint" style={{ fontSize: 11 }}>{kb(e.size)} · {e.uploaded_by}</span>
                </div>
                <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>{e.ai_summary}</div>
              </div>
              <a className="btn ghost" href={api.evidenceDownloadUrl(e.id)} target="_blank" rel="noreferrer">Open</a>
              {canInv && <button className="icon-btn" onClick={() => remove(e.id)}><Trash2 size={14} /></button>}
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}

/* ── Witnesses ─────────────────────────────────────────────────────── */
function WitnessTab({ cid, canInv, onChange, t }: any) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [form, setForm] = useState({ name: "", contact: "", statement: "", reliability: "Medium" });
  const load = () => { api.witnesses(cid).then(setRows); };
  useEffect(() => { load(); }, [cid]);

  const add = async () => {
    if (!form.name.trim()) return;
    await api.addWitness(cid, form);
    setForm({ name: "", contact: "", statement: "", reliability: "Medium" });
    await load(); await onChange();
  };

  return (
    <div className="grid" style={{ gap: 16 }}>
      {canInv &&
        <Panel title={<span><UserPlus size={13} /> {t("Record Witness")}</span> as any}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 120px", gap: 8, marginBottom: 8 }}>
            <input placeholder={t("Name")} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input placeholder={t("Contact (optional)")} value={form.contact} onChange={(e) => setForm({ ...form, contact: e.target.value })} />
            <select value={form.reliability} onChange={(e) => setForm({ ...form, reliability: e.target.value })}>
              <option>Low</option><option>Medium</option><option>High</option>
            </select>
          </div>
          <textarea placeholder={t("Statement…")} value={form.statement} rows={2}
            onChange={(e) => setForm({ ...form, statement: e.target.value })} style={{ width: "100%", marginBottom: 8 }} />
          <button className="btn primary" onClick={add}>{t("Add witness")}</button>
        </Panel>}
      <Panel title={t("Witnesses")} info={{ what: "Witnesses recorded during the investigation.", data: "witnesses (PII-masked by role)" }}>
        {!rows ? <Loading /> : rows.length === 0 ? <div className="faint">{t("No witnesses recorded.")}</div> :
          rows.map((w) => (
            <div key={w.id} style={{ padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <b>{w.name}</b><Chip kind={w.reliability}>{w.reliability} {t("reliability")}</Chip>
              </div>
              <div className="dim" style={{ fontSize: 13, marginTop: 4 }}>{w.statement || "No statement recorded."}</div>
              <div className="faint" style={{ fontSize: 11 }}>{w.contact} · {w.created_at?.slice(0, 10)}</div>
            </div>
          ))}
      </Panel>
    </div>
  );
}

/* ── Notes ─────────────────────────────────────────────────────────── */
function NotesTab({ cid, onChange, t }: any) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [text, setText] = useState("");
  const load = () => { api.notes(cid).then(setRows); };
  useEffect(() => { load(); }, [cid]);

  const add = async () => {
    if (!text.trim()) return;
    await api.addNote(cid, text); setText(""); await load(); await onChange();
  };
  const pin = async (n: any) => { await api.pinNote(n.id); await load(); };
  const del = async (n: any) => { await api.deleteNote(n.id); await load(); await onChange(); };

  return (
    <Panel title={t("Investigation Notebook")}
      info={{ what: "Timestamped case notes — auto-saved, pinnable, attributed to the author.", data: "case_notes" }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <textarea placeholder={t("Add a note… (Ctrl+Enter to save)")} value={text} rows={2}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => (e.ctrlKey && e.key === "Enter") && add()}
          style={{ flex: 1 }} />
        <button className="btn primary" onClick={add} disabled={!text.trim()}>{t("Save")}</button>
      </div>
      {!rows ? <Loading /> : rows.length === 0 ? <div className="faint">{t("No notes yet.")}</div> :
        rows.map((n) => (
          <div key={n.id} style={{ padding: "10px 12px", marginBottom: 8,
            border: "1px solid var(--border)", background: n.pinned ? "rgba(255,176,32,0.06)" : "var(--panel-2)",
            borderLeft: n.pinned ? "3px solid var(--amber)" : "1px solid var(--border)" }}>
            <div style={{ whiteSpace: "pre-wrap", fontSize: 13, lineHeight: 1.5 }}>{n.content}</div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
              <span className="faint" style={{ fontSize: 11 }}>
                {n.author} ({n.role}) · {new Date(n.created_at).toLocaleString()}
              </span>
              <span style={{ display: "flex", gap: 4 }}>
                <button className="icon-btn" title="Pin" onClick={() => pin(n)}
                  style={n.pinned ? { color: "var(--amber)", borderColor: "var(--amber)" } : {}}>
                  <Pin size={13} />
                </button>
                <button className="icon-btn" title="Delete" onClick={() => del(n)}><Trash2 size={13} /></button>
              </span>
            </div>
          </div>
        ))}
    </Panel>
  );
}

/* ── Timeline ──────────────────────────────────────────────────────── */
function TimelineTab({ c, t }: any) {
  return (
    <Panel title={<span><Clock size={13} /> {t("Case Timeline (system-generated)")}</span> as any}
      info={{ what: "Auto-logged events: FIR, evidence, notes, stage changes, witnesses.", data: "timeline_events", brief: "Case timeline (#3.6)" }}>
      <div style={{ display: "flex", flexDirection: "column" }}>
        {[...c.timeline].reverse().map((e: any, i: number) => (
          <div key={i} style={{ display: "flex", gap: 12, paddingBottom: 14 }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div style={{ width: 10, height: 10, background: "var(--accent)" }} />
              {i < c.timeline.length - 1 && <div style={{ width: 2, flex: 1, background: "var(--border-strong)" }} />}
            </div>
            <div>
              <div style={{ fontWeight: 600 }}>{e.title} <Chip>{e.type}</Chip></div>
              <div className="faint" style={{ fontSize: 12 }}>{e.timestamp?.slice(0, 16).replace("T", " ")}</div>
              <div className="dim" style={{ fontSize: 13, marginTop: 2 }}>{e.description}</div>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

/* ── AI Assistant (case-scoped) ────────────────────────────────────── */
function AITab({ c, t }: any) {
  const [q, setQ] = useState("");
  const [ans, setAns] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  const suggestions = [
    `Details of ${c.fir_number}`,
    c.accused[0] ? `Profile of ${c.accused[0].name}` : "Top repeat offenders",
    `Show hotspots for ${c.crime_type}`,
    `Predict ${c.crime_type} risk`,
  ];

  const ask = async (text: string) => {
    setBusy(true); setAns(null);
    try { setAns(await api.sendMessage(text)); } finally { setBusy(false); }
  };

  return (
    <Panel title={<span><Sparkles size={13} /> {t("Case AI Assistant")}</span> as any}
      info={{ what: "Ask the grounded AI about this case, its suspects, patterns and forecasts.", brief: "Conversational AI (#1)" }}>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
        {suggestions.map((s) => (
          <button key={s} className="chip accent" style={{ cursor: "pointer" }} onClick={() => ask(s)}>{s}</button>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <input placeholder={t("Ask about this case…")} value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && q.trim() && ask(q)} style={{ flex: 1 }} />
        <button className="btn primary" onClick={() => q.trim() && ask(q)} disabled={busy}>{t("Ask")}</button>
      </div>
      {busy && <Loading label={t("Analysing…")} />}
      {ans && (
        <div style={{ border: "1px solid var(--border)", background: "var(--panel-2)", padding: 12 }}>
          <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.55 }}>{ans.answer}</div>
          {ans.grounding?.status && (
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 10,
              padding: "6px 10px", border: "1px solid var(--border)", background: "var(--bg)",
              borderLeft: `3px solid ${ans.grounding.status === "GROUNDED" ? "var(--green)" : "var(--text-faint)"}` }}>
              <ShieldCheck size={14} style={{ color: ans.grounding.status === "GROUNDED" ? "var(--green)" : "var(--text-faint)" }} />
              <span style={{ fontSize: 12 }}>
                <b>{ans.grounding.status === "GROUNDED" ? t("Grounded") : t("Not a data claim")}</b>
                {ans.grounding.status === "GROUNDED" && <span className="faint"> · {ans.grounding.source_count} source(s) · {ans.grounding.confidence} confidence</span>}
              </span>
            </div>
          )}
        </div>
      )}
    </Panel>
  );
}

/* ── Similar cases ─────────────────────────────────────────────────── */
function SimilarTab({ similar, nav, t }: any) {
  if (!similar) return <Loading />;
  return (
    <Panel title={<span><GitCompare size={13} /> {t("Similar Past Cases")}</span> as any}
      info={{ what: "Past cases with matching crime type, MO and district — with outcomes.", data: "cases (scored)", brief: "Similar case search (#6)" }}>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead><tr><th>{t("FIR No.")}</th><th>{t("Title")}</th><th>{t("District")}</th><th>{t("Match")}</th><th>{t("Outcome")}</th></tr></thead>
          <tbody>
            {similar.similar.map((s: any) => (
              <tr key={s.id} style={{ cursor: "pointer" }} onClick={() => nav(`/cases/${s.id}`)}>
                <td className="mono" style={{ fontSize: 12 }}>{s.fir_number}</td>
                <td>{s.title}</td>
                <td className="dim">{s.district}</td>
                <td><Chip kind="accent">{s.match_score}%</Chip></td>
                <td><Chip>{s.outcome}</Chip></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
