import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft, MapPin, User, Clock, Users, GitCompare, FileDown, Upload,
  Pin, Trash2, Check, ChevronRight, ChevronLeft, Sparkles, ShieldCheck, FileText, UserPlus,
  Send, Paperclip, MessageSquare, Lock, Bot, UserCircle, PanelLeftOpen, PanelLeftClose,
  Search, ChevronDown, FolderOpen,
} from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { caseBriefing } from "../briefing";
import { Chip, Loading, Panel } from "../components";

const TABS = ["Overview", "Evidence", "Suspects", "Victims", "Witnesses", "Documents", "Notes", "Timeline", "Chargesheet", "AI Assistant", "Similar Cases"];

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
  const [sidebarOpen, setSidebarOpen] = useState(true);

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
    Suspects: bundle.counts.suspects, Victims: bundle.counts.victims,
  };

  return (
    <div style={{ display: "flex", gap: 0, height: "calc(100vh - 64px)", overflow: "hidden" }}>

      {/* ── Investigation Progress Sidebar ── */}
      <div style={{
        width: sidebarOpen ? 260 : 0, minWidth: sidebarOpen ? 260 : 0,
        borderRight: sidebarOpen ? "1px solid var(--border)" : "none",
        background: "var(--panel)", overflow: "hidden",
        transition: "width 0.25s ease, min-width 0.25s ease",
        display: "flex", flexDirection: "column",
      }}>
        {sidebarOpen && (
          <StageSidebar bundle={bundle} canInv={canInv} onChange={loadBundle} t={t} />
        )}
      </div>

      {/* ── Main content ── */}
      <div style={{ flex: 1, overflowY: "auto", overflowX: "hidden" }}>
        <div style={{ maxWidth: 960, margin: "0 auto", padding: "16px 20px" }}>

          {/* Top bar */}
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 16 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button className="btn ghost" style={{ width: "fit-content" }} onClick={() => nav("/cases")}>
                <ArrowLeft size={15} /> {t("Back")}
              </button>
              <button className="icon-btn" title={t("Toggle investigation sidebar")}
                onClick={() => setSidebarOpen(!sidebarOpen)}
                style={{ width: 32, height: 32, display: "flex", alignItems: "center", justifyContent: "center" }}>
                {sidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeftOpen size={16} />}
              </button>
            </div>
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

          {/* Tabs */}
          <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--border)", flexWrap: "wrap", marginTop: 16 }}>
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

          {/* Tab content — scrolls vertically */}
          <div style={{ paddingTop: 16, paddingBottom: 32 }}>
            {tab === "Overview" && <Overview c={c} inr={inr} nav={nav} t={t} />}
            {tab === "Evidence" && <EvidenceTab cid={cid} canInv={canInv} categories={bundle.evidence_categories} onChange={loadBundle} t={t} />}
            {tab === "Suspects" && <SuspectsTab c={c} nav={nav} t={t} />}
            {tab === "Victims" && <VictimsTab cid={cid} canInv={canInv} onChange={loadBundle} t={t} />}
            {tab === "Witnesses" && <WitnessTab cid={cid} canInv={canInv} onChange={loadBundle} t={t} />}
            {tab === "Documents" && <DocumentsTab cid={cid} t={t} />}
            {tab === "Notes" && <NotesTab cid={cid} onChange={loadBundle} t={t} />}
            {tab === "Timeline" && <TimelineTab c={c} t={t} />}
            {tab === "Chargesheet" && <ChargeSheetTab c={c} cid={cid} canInv={canInv} t={t} />}
            {tab === "AI Assistant" && <AITab c={c} cid={cid} t={t} />}
            {tab === "Similar Cases" && <SimilarTab similar={similar} nav={nav} t={t} />}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Stage Sidebar (vertical, collapsible) ────────────────────────── */
function approverFor(stageIndex: number): string {
  if (stageIndex <= 3) return "SHO";
  if (stageIndex <= 7) return "DSP";
  return "Commander";
}
const APPROVER_KN: Record<string, string> = {
  SHO: "SHO", DSP: "DSP", Commander: "Commander",
};
const APPROVER_LABEL: Record<string, string> = {
  SHO: "Requires SHO", DSP: "Requires DSP", Commander: "Requires Commander",
};

function StageSidebar({ bundle, canInv, onChange, t }: any) {
  const [busy, setBusy] = useState(false);
  const [requesting, setRequesting] = useState(false);
  const [comments, setComments] = useState("");
  const [sent, setSent] = useState(false);
  const stages: string[] = bundle.stages;
  const idx = bundle.stage_index;

  const advance = async (stage: string) => {
    setBusy(true);
    try { await api.setStage(bundle.case_id, stage); await onChange(); }
    finally { setBusy(false); }
  };

  const requestApproval = async () => {
    setBusy(true);
    try { await api.requestStage(bundle.case_id, stages[idx + 1], comments); setSent(true); setComments(""); }
    finally { setBusy(false); }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "16px 14px 12px", borderBottom: "1px solid var(--border)" }}>
        <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 1, color: "var(--text-faint)", marginBottom: 6 }}>
          {t("Investigation Progress")}
        </div>
        <div style={{ fontSize: 22, fontWeight: 700, color: "var(--accent)" }}>{bundle.progress}%</div>
        <div className="bar" style={{ marginTop: 6 }}><span style={{ width: `${bundle.progress}%` }} /></div>
        <div className="faint" style={{ fontSize: 11, marginTop: 4 }}>
          {bundle.remaining_stages} {t("stage(s) remaining")}
        </div>
      </div>

      {/* Vertical stage list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
        {stages.map((s: string, i: number) => {
          const done = i < idx, current = i === idx;
          const approver = approverFor(i);
          return (
            <div key={s}
              style={{ display: "flex", gap: 10, padding: "0 14px", cursor: canInv && !done && !current ? "pointer" : "default" }}
              onClick={() => canInv && !done && !current && advance(s)}>
              {/* Vertical connector line + dot */}
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", width: 20, flexShrink: 0 }}>
                <div style={{
                  width: 14, height: 14, borderRadius: "50%", flexShrink: 0,
                  border: `2px solid ${done ? "var(--green)" : current ? "var(--accent)" : "var(--border)"}`,
                  background: done ? "var(--green)" : current ? "var(--accent)" : "transparent",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  {done && <Check size={9} style={{ color: "#fff" }} />}
                  {current && <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#fff" }} />}
                </div>
                {i < stages.length - 1 && (
                  <div style={{
                    width: 2, flex: 1, minHeight: 20,
                    background: done ? "var(--green)" : "var(--border)",
                  }} />
                )}
              </div>
              {/* Label */}
              <div style={{ paddingBottom: 12, paddingTop: 0, minWidth: 0 }}>
                <div style={{
                  fontSize: 12, fontWeight: current ? 700 : 400, lineHeight: 1.3,
                  color: done ? "var(--green)" : current ? "var(--accent)" : "var(--text-dim)",
                }}>
                  {s}
                </div>
                <div style={{ fontSize: 10, color: "var(--text-faint)", marginTop: 1 }}>
                  {t(APPROVER_LABEL[approver])}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Action area */}
      <div style={{ padding: "10px 14px", borderTop: "1px solid var(--border)", flexShrink: 0 }}>
        {canInv ? (
          <>
            {idx < stages.length - 1 && (
              <button className="btn primary" disabled={busy} onClick={() => advance(stages[idx + 1])}
                style={{ width: "100%", fontSize: 12, marginBottom: 6 }}>
                {t("Advance")} <ChevronRight size={13} />
              </button>
            )}
            <select disabled={busy} value={bundle.current_stage}
              onChange={(e) => advance(e.target.value)}
              style={{ width: "100%", fontSize: 11 }}>
              {stages.map((s: string) => <option key={s} value={s}>{s}</option>)}
            </select>
          </>
        ) : (
          <>
            <div className="faint" style={{ fontSize: 11, marginBottom: 6 }}>
              {t("Your role can view progress but not change stages.")}
            </div>
            {idx < stages.length - 1 && !sent && (
              requesting ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <div className="faint" style={{ fontSize: 11 }}>
                    <Lock size={10} /> {t(APPROVER_LABEL[approverFor(idx + 1)])}
                  </div>
                  <textarea placeholder={t("Reason for access request…")} value={comments} rows={2}
                    onChange={(e) => setComments(e.target.value)} style={{ width: "100%", fontSize: 12 }} />
                  <button className="btn primary" disabled={busy} onClick={requestApproval}
                    style={{ fontSize: 12 }}>{t("Request Approval")}</button>
                  <button className="btn ghost" onClick={() => setRequesting(false)}
                    style={{ fontSize: 12 }}>{t("Back")}</button>
                </div>
              ) : (
                <button className="btn ghost" onClick={() => setRequesting(true)}
                  style={{ width: "100%", fontSize: 11 }}>
                  <Lock size={11} /> {t("Request Approval")}
                </button>
              )
            )}
            {sent && <div className="faint" style={{ fontSize: 11 }}>{t("Pending approval")}</div>}
          </>
        )}
      </div>
    </div>
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
  const [evidenceName, setEvidenceName] = useState("");
  const [details, setDetails] = useState("");
  const [remarks, setRemarks] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const load = () => api.evidence(cid).then(setRows);
  useEffect(() => { load(); }, [cid]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setSelectedFile(f);
  };

  const upload = async () => {
    if (!selectedFile) return;
    setBusy(true);
    const fullRemarks = [evidenceName && `Name: ${evidenceName}`, details && `Details: ${details}`, remarks].filter(Boolean).join("\n");
    try {
      await api.uploadEvidenceWithRemarks(cid, category, selectedFile, fullRemarks);
      setRemarks(""); setEvidenceName(""); setDetails(""); setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = "";
      await load(); await onChange();
    }
    finally { setBusy(false); }
  };
  const remove = async (docId: number) => { await api.deleteEvidence(docId); await load(); await onChange(); };
  const kb = (n: number) => n > 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;
  const [previewId, setPreviewId] = useState<number | null>(null);
  const isPreviewable = (name: string) => /\.(jpe?g|png|gif|webp|bmp|svg|pdf)$/i.test(name);
  const isPdf = (name: string) => /\.pdf$/i.test(name);

  return (
    <div className="grid" style={{ gap: 16 }}>
      {!canInv && <RequestAccessPanel cid={cid} t={t} />}
      {canInv && (
        <Panel title={<span><Upload size={13} /> {t("Upload Evidence")}</span> as any}>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            style={{
              border: dragOver ? "2px dashed var(--accent)" : "2px dashed transparent",
              borderRadius: 8, padding: dragOver ? 12 : 0,
              background: dragOver ? "rgba(0,209,255,0.06)" : "transparent",
              transition: "all 0.2s",
            }}
          >
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
              <input placeholder={t("Evidence name")} value={evidenceName}
                onChange={(e) => setEvidenceName(e.target.value)} />
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {categories.map((c: string) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <textarea placeholder={t("Details (what, where, how it was collected)…")} value={details} rows={2}
              onChange={(e) => setDetails(e.target.value)} style={{ width: "100%", marginBottom: 8 }} />
            <textarea placeholder={t("Remarks / description…")} value={remarks} rows={2}
              onChange={(e) => setRemarks(e.target.value)} style={{ width: "100%", marginBottom: 8 }} />
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <label className="btn ghost" style={{ cursor: "pointer" }}>
                <Paperclip size={14} /> {selectedFile ? selectedFile.name : t("Choose file")}
                <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.csv,.xlsx,.xls" hidden onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
              </label>
              {selectedFile && <button className="icon-btn" onClick={() => { setSelectedFile(null); if (fileRef.current) fileRef.current.value = ""; }}><Trash2 size={12} /></button>}
              <div style={{ flex: 1 }} />
              {!selectedFile && <span className="faint" style={{ fontSize: 11 }}>{t("or drag & drop a file here")}</span>}
              <button className="btn primary" onClick={upload} disabled={busy || !selectedFile}>
                <Upload size={14} /> {busy ? t("Uploading…") : t("Upload Evidence")}
              </button>
            </div>
          </div>
        </Panel>
      )}
      <Panel title={t("Evidence & Documents")}
        info={{ what: "Upload, categorise and preview case documents. Each gets an AI summary.", data: "evidence_documents", brief: "Evidence management (#6)" }}>
        {!rows ? <Loading /> : rows.length === 0 ? <div className="faint center" style={{ padding: 24 }}>{t("No evidence uploaded yet.")}</div> : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {rows.map((e) => (
              <div key={e.id}>
                <div style={{ display: "flex", gap: 12, alignItems: "start", padding: "10px 12px",
                  border: "1px solid var(--border)", background: "var(--panel-2)" }}>
                  <FileText size={18} className="dim" style={{ marginTop: 2 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                      <b style={{ wordBreak: "break-word" }}>{e.original_name}</b><Chip kind="accent">{e.category}</Chip>
                      <span className="faint" style={{ fontSize: 11 }}>{kb(e.size)} · {e.uploaded_by}</span>
                    </div>
                    <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>{e.ai_summary}</div>
                    {e.remarks && <div className="faint" style={{ fontSize: 12, marginTop: 2, fontStyle: "italic", whiteSpace: "pre-line" }}>{e.remarks}</div>}
                  </div>
                  {isPreviewable(e.original_name) && (
                    <button className="btn ghost" style={{ fontSize: 12 }}
                      onClick={() => setPreviewId(previewId === e.id ? null : e.id)}>
                      {previewId === e.id ? t("Hide") : t("Preview")}
                    </button>
                  )}
                  <a className="btn ghost" href={api.evidenceDownloadUrl(e.id)} target="_blank" rel="noreferrer">Open</a>
                  {canInv && <button className="icon-btn" onClick={() => remove(e.id)}><Trash2 size={14} /></button>}
                </div>
                {previewId === e.id && (
                  <div style={{ padding: "8px 12px", border: "1px solid var(--border)", borderTop: "none",
                    background: "var(--bg)", textAlign: "center" }}>
                    {isPdf(e.original_name) ? (
                      <iframe src={api.evidenceDownloadUrl(e.id)} style={{ width: "100%", height: 400, border: "1px solid var(--border)" }} title={e.original_name} />
                    ) : (
                      <img src={api.evidenceDownloadUrl(e.id)} alt={e.original_name}
                        style={{ maxWidth: "100%", maxHeight: 400, objectFit: "contain", border: "1px solid var(--border)" }} />
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}

/* ── Witnesses ─────────────────────────────────────────────────────── */
function WitnessTab({ cid, canInv, onChange, t }: any) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [form, setForm] = useState({ name: "", contact: "", statement: "", reliability: "Medium" });
  const [docFile, setDocFile] = useState<File | null>(null);
  const load = () => api.witnesses(cid).then(setRows);
  useEffect(() => { load(); }, [cid]);

  const add = async () => {
    if (!form.name.trim()) return;
    await api.addWitnessWithFile(cid, form, docFile || undefined);
    setForm({ name: "", contact: "", statement: "", reliability: "Medium" });
    setDocFile(null);
    await load(); await onChange();
  };

  return (
    <div className="grid" style={{ gap: 16 }}>
      {!canInv && <RequestAccessPanel cid={cid} t={t} />}
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
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
            <label className="btn ghost" style={{ cursor: "pointer" }}>
              <FileText size={14} /> {docFile ? docFile.name : t("Attach document (optional)")}
              <input type="file" hidden onChange={(e) => setDocFile(e.target.files?.[0] || null)} />
            </label>
            {docFile && <button className="icon-btn" onClick={() => setDocFile(null)}><Trash2 size={12} /></button>}
          </div>
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
              {w.document_name && (
                <a className="faint" style={{ fontSize: 11, display: "inline-flex", alignItems: "center", gap: 4, marginTop: 4 }}
                  href={api.evidenceDownloadUrl(w.document_id)} target="_blank" rel="noreferrer">
                  <FileText size={11} /> {w.document_name}
                </a>
              )}
            </div>
          ))}
      </Panel>
    </div>
  );
}

/* ── Request access panel ──────────────────────────────────────────── */
function RequestAccessPanel({ cid, t }: any) {
  const { user } = useAuth();
  const [reason, setReason] = useState("");
  const [sent, setSent] = useState(false);
  const [emergencyMode, setEmergencyMode] = useState(false);
  const canEmergency = ["dsp", "commander"].includes(user?.role || "");

  const submit = async () => {
    if (!reason.trim()) return;
    await api.requestAccess(cid, reason);
    setSent(true);
  };

  const submitEmergency = async () => {
    if (!reason.trim()) return;
    await api.emergencyAccess(cid, reason);
    setSent(true);
    window.location.reload();
  };

  if (sent) return <div className="faint center" style={{ padding: 20 }}>{
    emergencyMode ? t("Emergency access granted. This action has been logged for audit.")
      : t("Access request submitted. Awaiting approval from SHO/DSP.")
  }</div>;
  return (
    <Panel title={t("Request Investigation Access")}>
      <p className="dim">{t("Your current role does not have investigation permissions for this case.")}</p>
      <textarea placeholder={t("Reason for access request…")} value={reason} rows={2}
        onChange={(e) => setReason(e.target.value)} style={{ width: "100%", marginBottom: 8 }} />
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <button className="btn primary" onClick={submit} disabled={!reason.trim()}>{t("Submit Request")}</button>
        {canEmergency && (
          <button className="btn ghost" onClick={() => { setEmergencyMode(true); submitEmergency(); }}
            disabled={!reason.trim()}
            style={{ borderColor: "var(--red, #e53e3e)", color: "var(--red, #e53e3e)" }}>
            {t("Emergency Override")}
          </button>
        )}
      </div>
      {canEmergency && <p className="faint" style={{ fontSize: 11, marginTop: 6 }}>
        {t("Emergency override grants immediate access. This action is logged and audited.")}
      </p>}
    </Panel>
  );
}

/* ── Notes ─────────────────────────────────────────────────────────── */
function NotesTab({ cid, onChange, t }: any) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [text, setText] = useState("");
  const load = () => api.notes(cid).then(setRows);
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
              <div style={{ width: 10, height: 10, background: "var(--accent)", borderRadius: "50%" }} />
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

/* ── AI Assistant (polished chat UI) ──────────────────────────────── */
function AITab({ c, cid, t }: any) {
  const [messages, setMessages] = useState<any[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  const suggestions = [
    `Details of ${c.fir_number}`,
    c.accused[0] ? `Profile of ${c.accused[0].name}` : "Top repeat offenders",
    `Show hotspots for ${c.crime_type}`,
    `Predict ${c.crime_type} risk`,
  ];

  useEffect(() => {
    api.caseChat(cid).then((data: any) => {
      setMessages(data.messages || []);
    }).catch(() => {}).finally(() => setLoaded(true));
  }, [cid]);

  useEffect(() => {
    chatRef.current?.scrollTo(0, chatRef.current.scrollHeight);
  }, [messages, busy]);

  const ask = async (text: string) => {
    if (!text.trim()) return;
    const displayMsg = file ? `[Attached: ${file.name}] ${text}` : text;
    const attachedFile = file;
    setMessages((prev) => [...prev, { role: "user", content: displayMsg, created_at: new Date().toISOString() }]);
    setBusy(true); setQ(""); setFile(null);
    try {
      const res = await api.caseChatSend(cid, text, attachedFile || undefined);
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer, grounding: res.grounding, created_at: new Date().toISOString() }]);
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Error processing request.", created_at: new Date().toISOString() }]);
    } finally { setBusy(false); }
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column",
      border: "1px solid var(--border)", borderRadius: 10, overflow: "hidden",
      background: "var(--panel)",
    }}>
      {/* Chat header */}
      <div style={{
        padding: "14px 18px", display: "flex", alignItems: "center", gap: 10,
        background: "linear-gradient(135deg, rgba(0,209,255,0.12), rgba(0,209,255,0.04))",
        borderBottom: "1px solid var(--border)",
      }}>
        <div style={{
          width: 36, height: 36, borderRadius: "50%",
          background: "linear-gradient(135deg, var(--accent), rgba(0,209,255,0.5))",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <Sparkles size={18} style={{ color: "#fff" }} />
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 14 }}>{t("Case AI Assistant")}</div>
          <div className="faint" style={{ fontSize: 11 }}>
            {busy ? t("Analysing…") : t("Ask about this case, suspects, patterns & forecasts")}
          </div>
        </div>
      </div>

      {/* Suggestion chips */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6, padding: "10px 16px",
        borderBottom: "1px solid var(--border)", background: "var(--panel-2)" }}>
        {suggestions.map((s) => (
          <button key={s} onClick={() => ask(s)} disabled={busy}
            style={{
              padding: "4px 10px", fontSize: 11, border: "1px solid var(--border)",
              borderRadius: 14, background: "var(--panel)", color: "var(--accent)",
              cursor: busy ? "not-allowed" : "pointer", opacity: busy ? 0.5 : 1,
            }}>{s}</button>
        ))}
      </div>

      {/* Messages area */}
      <div ref={chatRef} style={{
        flex: 1, display: "flex", flexDirection: "column", gap: 4,
        minHeight: 340, maxHeight: "calc(100vh - 500px)", overflowY: "auto",
        padding: "16px 16px 8px", background: "var(--bg)",
      }}>
        {!loaded ? <Loading label={t("Analysing…")} /> :
          messages.length === 0 ? (
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center",
              justifyContent: "center", flex: 1, gap: 8, opacity: 0.5 }}>
              <MessageSquare size={28} />
              <div style={{ fontSize: 13 }}>{t("No conversations yet.")}</div>
              <div className="faint" style={{ fontSize: 11 }}>{t("Click a suggestion above or type a question")}</div>
            </div>
          ) : messages.map((m, i) => {
            const isUser = m.role === "user";
            return (
              <div key={i} style={{
                display: "flex", gap: 8,
                flexDirection: isUser ? "row-reverse" : "row",
                marginBottom: 8,
              }}>
                {/* Avatar */}
                <div style={{
                  width: 30, height: 30, borderRadius: "50%", flexShrink: 0,
                  background: isUser ? "rgba(0,209,255,0.15)" : "linear-gradient(135deg, var(--accent), rgba(0,209,255,0.5))",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  marginTop: 2,
                }}>
                  {isUser
                    ? <UserCircle size={16} style={{ color: "var(--accent)" }} />
                    : <Bot size={16} style={{ color: "#fff" }} />}
                </div>
                {/* Bubble */}
                <div style={{
                  maxWidth: "80%", minWidth: 60,
                  padding: "10px 14px",
                  borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                  background: isUser ? "rgba(0,209,255,0.1)" : "var(--panel)",
                  border: `1px solid ${isUser ? "rgba(0,209,255,0.25)" : "var(--border)"}`,
                }}>
                  <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.55, fontSize: 13 }}>{m.content}</div>
                  {m.grounding?.status && (
                    <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 8,
                      padding: "4px 8px", borderRadius: 6,
                      border: "1px solid var(--border)", background: "var(--bg)",
                      borderLeft: `3px solid ${m.grounding.status === "GROUNDED" ? "var(--green)" : "var(--text-faint)"}` }}>
                      <ShieldCheck size={12} style={{ color: m.grounding.status === "GROUNDED" ? "var(--green)" : "var(--text-faint)" }} />
                      <span style={{ fontSize: 11 }}>
                        <b>{m.grounding.status === "GROUNDED" ? t("Grounded") : t("Not a data claim")}</b>
                        {m.grounding.status === "GROUNDED" && <span className="faint"> · {m.grounding.source_count} source(s) · {m.grounding.confidence} confidence</span>}
                      </span>
                    </div>
                  )}
                  {m.created_at && <div className="faint" style={{ fontSize: 10, marginTop: 6 }}>{new Date(m.created_at).toLocaleString()}</div>}
                </div>
              </div>
            );
          })}
        {/* Typing indicator */}
        {busy && (
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            <div style={{
              width: 30, height: 30, borderRadius: "50%", flexShrink: 0,
              background: "linear-gradient(135deg, var(--accent), rgba(0,209,255,0.5))",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              <Bot size={16} style={{ color: "#fff" }} />
            </div>
            <div style={{
              padding: "12px 18px", borderRadius: "14px 14px 14px 4px",
              background: "var(--panel)", border: "1px solid var(--border)",
              display: "flex", gap: 4, alignItems: "center",
            }}>
              <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "typingBounce 1.2s infinite", animationDelay: "0ms" }} />
              <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "typingBounce 1.2s infinite", animationDelay: "200ms" }} />
              <span className="typing-dot" style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--accent)", animation: "typingBounce 1.2s infinite", animationDelay: "400ms" }} />
            </div>
          </div>
        )}
      </div>

      {/* File attachment indicator */}
      {file && (
        <div style={{ padding: "6px 16px", background: "var(--panel-2)", borderTop: "1px solid var(--border)",
          display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
          <Paperclip size={12} className="faint" />
          <span style={{ flex: 1 }}>{file.name}</span>
          <button className="icon-btn" onClick={() => setFile(null)} style={{ width: 22, height: 22 }}><Trash2 size={11} /></button>
        </div>
      )}

      {/* Input bar */}
      <div style={{
        display: "flex", gap: 8, alignItems: "center",
        padding: "10px 14px", borderTop: "1px solid var(--border)",
        background: "var(--panel)",
      }}>
        <label style={{ cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
          width: 34, height: 34, borderRadius: "50%", border: "1px solid var(--border)",
          background: "var(--panel-2)", flexShrink: 0 }}
          title={t("Attach file for analysis")}>
          <Paperclip size={15} className="dim" />
          <input type="file" accept=".pdf,.docx,.txt,.csv,.xlsx,.xls" hidden onChange={(e) => setFile(e.target.files?.[0] || null)} />
        </label>
        <input placeholder={t("Ask about this case…")} value={q} onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && q.trim() && ask(q)}
          disabled={busy}
          style={{
            flex: 1, borderRadius: 20, padding: "8px 16px",
            border: "1px solid var(--border)", background: "var(--bg)",
            fontSize: 13,
          }} />
        <button onClick={() => ask(q)} disabled={busy || !q.trim()}
          style={{
            width: 36, height: 36, borderRadius: "50%", border: "none",
            background: q.trim() && !busy ? "var(--accent)" : "var(--border)",
            color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
            cursor: q.trim() && !busy ? "pointer" : "not-allowed", flexShrink: 0,
          }}>
          <Send size={15} />
        </button>
      </div>
    </div>
  );
}

/* ── Suspects ─────────────────────────────────────────────────────── */
function SuspectsTab({ c, nav, t }: any) {
  return (
    <Panel title={<span><Users size={13} /> {t("Suspects / Accused")}</span> as any}>
      {c.accused.length === 0 ? <div className="faint center" style={{ padding: 24 }}>{t("None recorded.")}</div> : (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead><tr><th>{t("Name")}</th><th>{t("Role")}</th><th>{t("Status")}</th><th /></tr></thead>
            <tbody>
              {c.accused.map((a: any) => (
                <tr key={a.id} style={{ cursor: "pointer" }} onClick={() => nav(`/offender/${a.id}`)}>
                  <td><User size={13} style={{ marginRight: 6 }} />{a.name}</td>
                  <td><Chip>{a.role}</Chip></td>
                  <td><Chip kind="amber">{a.status}</Chip></td>
                  <td style={{ textAlign: "right" }}><ChevronRight size={14} className="dim" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}

/* ── Victims ──────────────────────────────────────────────────────── */
function VictimsTab({ cid, canInv, onChange, t }: any) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [form, setForm] = useState({ full_name: "", gender: "Male", age: "", contact_number: "", address: "", occupation: "", statement_summary: "" });
  const [busy, setBusy] = useState(false);
  const load = () => api.caseVictims(cid).then(setRows);
  useEffect(() => { load(); }, [cid]);

  const add = async () => {
    if (!form.full_name.trim()) return;
    setBusy(true);
    await api.addVictim(cid, { ...form, age: form.age ? Number(form.age) : 0 });
    setForm({ full_name: "", gender: "Male", age: "", contact_number: "", address: "", occupation: "", statement_summary: "" });
    setBusy(false);
    await load(); await onChange();
  };

  const remove = async (victimId: number) => {
    await api.unlinkVictim(cid, victimId);
    await load(); await onChange();
  };

  return (
    <div className="grid" style={{ gap: 16 }}>
      {!canInv && <RequestAccessPanel cid={cid} t={t} />}
      {canInv && (
        <Panel title={<span><UserPlus size={13} /> {t("Add Victim")}</span> as any}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 100px 70px", gap: 8, marginBottom: 8 }}>
            <input placeholder={t("Name")} value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
              <option>Male</option><option>Female</option><option>Other</option>
            </select>
            <input type="number" placeholder={t("Age")} value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
            <input placeholder={t("Contact (optional)")} value={form.contact_number} onChange={(e) => setForm({ ...form, contact_number: e.target.value })} />
            <input placeholder={t("Occupation")} value={form.occupation} onChange={(e) => setForm({ ...form, occupation: e.target.value })} />
          </div>
          <input placeholder={t("Address")} value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })}
            style={{ width: "100%", marginBottom: 8 }} />
          <textarea placeholder={t("Statement…")} value={form.statement_summary} rows={2}
            onChange={(e) => setForm({ ...form, statement_summary: e.target.value })} style={{ width: "100%", marginBottom: 8 }} />
          <button className="btn primary" onClick={add} disabled={busy || !form.full_name.trim()}>
            {busy ? t("Saving…") : t("Add Victim")}
          </button>
        </Panel>
      )}
      <Panel title={<span><User size={13} /> {t("Victims")}</span> as any}>
        {!rows ? <Loading /> : rows.length === 0 ? <div className="faint center" style={{ padding: 24 }}>{t("None recorded.")}</div> : (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>{t("Name")}</th><th>{t("Age/Gender")}</th><th>{t("District")}</th>
                  <th>{t("Contact")}</th><th>{t("Cases")}</th>
                  {canInv && <th></th>}
                </tr>
              </thead>
              <tbody>
                {rows.map((v: any) => (
                  <tr key={v.id}>
                    <td style={{ fontWeight: 600 }}>{v.name}</td>
                    <td className="dim">{v.age || "–"} / {v.gender || "–"}</td>
                    <td className="dim">{v.district || "–"}</td>
                    <td className="dim">{v.contact || "–"}</td>
                    <td><Chip kind={v.case_count > 1 ? "High" : "Low"}>{v.case_count} {t("case(s)")}</Chip></td>
                    {canInv && (
                      <td>
                        <button className="icon-btn" title="Unlink" onClick={() => remove(v.id)}>
                          <Trash2 size={12} />
                        </button>
                      </td>
                    )}
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

/* ── Documents (grouped evidence) ─────────────────────────────────── */
function DocumentsTab({ cid, t }: any) {
  const [rows, setRows] = useState<any[] | null>(null);
  const [search, setSearch] = useState("");
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  useEffect(() => { api.evidence(cid).then(setRows); }, [cid]);

  if (!rows) return <Loading />;

  const filtered = search
    ? rows.filter((e) => e.original_name?.toLowerCase().includes(search.toLowerCase()))
    : rows;

  const grouped: Record<string, any[]> = {};
  for (const e of filtered) {
    const cat = e.category || "Uncategorised";
    (grouped[cat] ??= []).push(e);
  }
  const categories = Object.keys(grouped).sort();

  const toggle = (cat: string) => setCollapsed((p) => ({ ...p, [cat]: !p[cat] }));

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div style={{ position: "relative" }}>
        <Search size={14} style={{ position: "absolute", left: 10, top: 10, color: "var(--text-faint)" }} />
        <input placeholder={t("Search documents…")} value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: "100%", paddingLeft: 32 }} />
      </div>
      {categories.length === 0 ? (
        <div className="faint center" style={{ padding: 24 }}>{t("No evidence uploaded yet.")}</div>
      ) : categories.map((cat) => (
        <Panel key={cat}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
            onClick={() => toggle(cat)}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 600 }}>
              <FolderOpen size={15} />
              {cat}
              <span className="faint" style={{ fontWeight: 400, fontSize: 12 }}>({grouped[cat].length})</span>
            </div>
            <ChevronDown size={14} style={{
              transition: "transform 0.2s",
              transform: collapsed[cat] ? "rotate(-90deg)" : "rotate(0deg)",
            }} />
          </div>
          {!collapsed[cat] && (
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 10 }}>
              {grouped[cat].map((e) => (
                <div key={e.id} style={{ display: "flex", gap: 10, alignItems: "center", padding: "6px 8px",
                  border: "1px solid var(--border)", background: "var(--panel-2)" }}>
                  <FileText size={15} className="dim" />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 500, wordBreak: "break-word", fontSize: 13 }}>{e.original_name}</div>
                    {e.ai_summary && <div className="dim" style={{ fontSize: 11, marginTop: 2 }}>{e.ai_summary}</div>}
                  </div>
                  <a className="btn ghost" href={api.evidenceDownloadUrl(e.id)} target="_blank" rel="noreferrer"
                    style={{ fontSize: 11, flexShrink: 0 }}>Open</a>
                </div>
              ))}
            </div>
          )}
        </Panel>
      ))}
    </div>
  );
}

/* ── Chargesheet ──────────────────────────────────────────────────── */
function ChargeSheetTab({ c, cid, canInv, t }: any) {
  const [cs, setCs] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const generate = async () => {
    setBusy(true); setError("");
    try {
      const res = await api.generateChargesheet(cid);
      if (res.detail) { setError(res.detail); } else { setCs(res); }
    } catch (e: any) { setError(e.message || "Error"); }
    finally { setBusy(false); }
  };

  if (!cs) {
    return (
      <Panel title={t("Chargesheet Generation")}>
        <div style={{ textAlign: "center", padding: "30px 0" }}>
          <FileText size={36} className="dim" />
          <p className="dim" style={{ marginTop: 12 }}>{t("Generate a chargesheet draft with all case details auto-populated.")}</p>
          <p className="faint" style={{ fontSize: 12 }}>{t("Includes accused, victims, witnesses, evidence, and applicable BNS/IPC sections.")}</p>
          {error && <div style={{ color: "var(--red, #e53e3e)", fontSize: 13, margin: "10px 0" }}>{error}</div>}
          {canInv ? (
            <button className="btn primary" onClick={generate} disabled={busy} style={{ marginTop: 16 }}>
              <FileText size={14} /> {busy ? t("Generating...") : t("Generate Chargesheet")}
            </button>
          ) : (
            <div className="faint" style={{ marginTop: 16, fontSize: 12 }}>{t("Investigation permission required to generate chargesheet.")}</div>
          )}
        </div>
      </Panel>
    );
  }

  return (
    <div className="grid" style={{ gap: 16 }}>
      <Panel>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h3 style={{ margin: 0 }}>{t("Chargesheet Draft")}</h3>
            <div className="faint" style={{ fontSize: 12, marginTop: 2 }}>
              {t("Generated")} {new Date(cs.generated_at).toLocaleString()} {t("by")} {cs.generated_by}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <Chip kind="amber">{cs.status}</Chip>
            <button className="btn ghost" onClick={generate} disabled={busy} style={{ fontSize: 12 }}>
              {busy ? t("Regenerating...") : t("Regenerate")}
            </button>
          </div>
        </div>
      </Panel>

      <div className="grid cols-2">
        <Panel title={t("Case Information")}>
          <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "6px 16px", fontSize: 13 }}>
            <span className="faint">{t("FIR No.")}</span><span className="mono">{cs.fir_number}</span>
            <span className="faint">{t("Title")}</span><span>{cs.title}</span>
            <span className="faint">{t("Crime Type")}</span><span>{cs.crime_type}</span>
            <span className="faint">{t("District")}</span><span>{cs.district}</span>
            <span className="faint">{t("Police Station")}</span><span>{cs.station || "—"}</span>
            <span className="faint">{t("Date of Occurrence")}</span><span>{cs.occurrence_date?.slice(0, 10) || "—"}</span>
            <span className="faint">{t("Date Reported")}</span><span>{cs.reported_date?.slice(0, 10) || "—"}</span>
            <span className="faint">{t("IO")}</span><span>{cs.investigating_officer || "—"}</span>
          </div>
        </Panel>

        <Panel title={t("Applicable Sections")}>
          {cs.applicable_sections.length === 0 ? <div className="faint">{t("No sections mapped.")}</div> : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {cs.applicable_sections.map((s: any, i: number) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid var(--border)" }}>
                  <Chip kind="accent">{s.code}</Chip>
                  <span className="dim" style={{ fontSize: 12 }}>{s.description}</span>
                </div>
              ))}
            </div>
          )}
        </Panel>
      </div>

      {cs.investigation_summary && (
        <Panel title={t("Investigation Summary")}>
          <p className="dim" style={{ lineHeight: 1.6, margin: 0 }}>{cs.investigation_summary}</p>
        </Panel>
      )}

      <div className="grid cols-2">
        <Panel title={`${t("Accused")} (${cs.accused.length})`}>
          {cs.accused.length === 0 ? <div className="faint">{t("None recorded.")}</div> : (
            <table>
              <thead><tr><th>{t("Name")}</th><th>{t("Role")}</th><th>{t("Status")}</th></tr></thead>
              <tbody>
                {cs.accused.map((a: any) => (
                  <tr key={a.id}><td>{a.name}</td><td><Chip>{a.role}</Chip></td><td><Chip kind="amber">{a.status}</Chip></td></tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <Panel title={`${t("Victims")} (${cs.victims.length})`}>
          {cs.victims.length === 0 ? <div className="faint">{t("None recorded.")}</div> : (
            <table>
              <thead><tr><th>{t("Name")}</th><th>{t("Age")}</th><th>{t("Gender")}</th></tr></thead>
              <tbody>
                {cs.victims.map((v: any) => (
                  <tr key={v.id}><td>{v.name}</td><td>{v.age || "—"}</td><td>{v.gender || "—"}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>

      <div className="grid cols-2">
        <Panel title={`${t("Witnesses")} (${cs.witnesses.length})`}>
          {cs.witnesses.length === 0 ? <div className="faint">{t("None recorded.")}</div> : (
            <table>
              <thead><tr><th>{t("Name")}</th><th>{t("Reliability")}</th></tr></thead>
              <tbody>
                {cs.witnesses.map((w: any) => (
                  <tr key={w.id}><td>{w.name}</td><td><Chip kind={w.reliability}>{w.reliability}</Chip></td></tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>

        <Panel title={`${t("Evidence")} (${cs.evidence.length})`}>
          {cs.evidence.length === 0 ? <div className="faint">{t("No evidence uploaded yet.")}</div> : (
            <table>
              <thead><tr><th>{t("Document")}</th><th>{t("Category")}</th></tr></thead>
              <tbody>
                {cs.evidence.map((e: any) => (
                  <tr key={e.id}><td>{e.filename}</td><td><Chip kind="accent">{e.category}</Chip></td></tr>
                ))}
              </tbody>
            </table>
          )}
        </Panel>
      </div>
    </div>
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
