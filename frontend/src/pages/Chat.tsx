import { useEffect, useRef, useState } from "react";
import {
  Send, Mic, MicOff, Volume2, FileDown, Plus, Trash2, Code2, Database,
  Sparkles, ChevronDown, ChevronRight, ShieldCheck, GitBranch, ArrowRight,
} from "lucide-react";
import jsPDF from "jspdf";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { BarViz, LineViz, Chip } from "../components";
import { toKannada } from "../kannada";

const PROV_KIND: Record<string, string> = {
  DATABASE_FACT: "green", COMPUTED_FINDING: "accent",
  MODEL_PREDICTION: "amber", MODEL_HYPOTHESIS: "Critical",
};
const PROV_LABEL: Record<string, string> = {
  DATABASE_FACT: "Database fact", COMPUTED_FINDING: "Computed",
  MODEL_PREDICTION: "Model prediction", MODEL_HYPOTHESIS: "Hypothesis",
};

interface Msg {
  role: "user" | "assistant";
  content: string;
  sql?: string;
  intent?: string;
  evidence?: { table: string; detail: string; provenance?: string }[];
  grounding?: any;
  reasoning?: { step: string; detail: string; icon?: string }[];
  data?: any;
  language?: string;
}

const SUGGESTIONS = [
  "How many cyber fraud cases in Bengaluru City?",
  "Show crime trend over time",
  "Top repeat offenders",
  "Show hotspots for chain snatching",
  "Predict crime for next week",
  "Show the money trail summary",
];

export default function Chat() {
  const { user } = useAuth();
  const { t } = useLang();
  const [convs, setConvs] = useState<any[]>([]);
  const [convId, setConvId] = useState<number | undefined>();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [lang, setLang] = useState<"auto" | "en" | "kn">("auto");
  const [listening, setListening] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const recogRef = useRef<any>(null);

  useEffect(() => { loadConvs(); }, []);
  useEffect(() => { scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight); }, [msgs, busy]);

  const loadConvs = () => api.conversations().then(setConvs).catch(() => {});

  const openConv = async (id: number) => {
    const c = await api.conversation(id);
    setConvId(id);
    setMsgs(c.messages.map((m: any) => ({
      role: m.role, content: m.content, sql: m.sql, intent: m.intent,
      evidence: m.evidence, grounding: m.grounding, reasoning: m.reasoning, language: m.language,
    })));
  };

  const newConv = () => { setConvId(undefined); setMsgs([]); };

  const removeConv = async (id: number, e: any) => {
    e.stopPropagation();
    await api.deleteConversation(id);
    if (id === convId) newConv();
    loadConvs();
  };

  const knTyping = lang === "kn";
  const preview = knTyping && input ? toKannada(input) : "";

  const send = async (text?: string) => {
    let message = (text ?? input).trim();
    if (!message || busy) return;
    if (knTyping && !text) message = toKannada(message);
    setInput("");
    setMsgs((m) => [...m, { role: "user", content: message, language: lang }]);
    setBusy(true);
    try {
      const r = await api.sendMessage(message, convId, lang);
      if (!convId) { setConvId(r.conversation_id); loadConvs(); }
      const am: Msg = {
        role: "assistant", content: r.answer, sql: r.sql, intent: r.intent,
        evidence: r.evidence, grounding: r.grounding, reasoning: r.reasoning,
        data: r.data, language: r.language,
      };
      setMsgs((m) => [...m, am]);
    } catch (e: any) {
      setMsgs((m) => [...m, { role: "assistant", content: "Error: " + e.message }]);
    } finally { setBusy(false); }
  };

  const toggleMic = () => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) { alert("Voice recognition is not supported in this browser (try Chrome/Edge)."); return; }
    if (listening) { recogRef.current?.stop(); return; }
    const r = new SR();
    r.lang = lang === "kn" ? "kn-IN" : "en-IN";
    r.interimResults = false;
    r.onresult = (e: any) => { const txt = e.results[0][0].transcript; setInput(txt); setTimeout(() => send(txt), 100); };
    r.onend = () => setListening(false);
    r.onerror = () => setListening(false);
    recogRef.current = r; r.start(); setListening(true);
  };

  const speak = (text: string, l?: string) => {
    const u = new SpeechSynthesisUtterance(text);
    u.lang = l === "kn" ? "kn-IN" : "en-IN";
    speechSynthesis.cancel(); speechSynthesis.speak(u);
  };

  const exportPdf = () => {
    const doc = new jsPDF();
    const W = doc.internal.pageSize.getWidth();
    let y = 18;
    doc.setFontSize(16); doc.setTextColor(20, 30, 50);
    doc.text("Crime Intelligence — Conversation Transcript", 14, y); y += 7;
    doc.setFontSize(9); doc.setTextColor(120);
    doc.text(`Exported by ${user?.full_name} (${user?.role}) · ${new Date().toLocaleString()}`, 14, y);
    y += 4; doc.setDrawColor(200); doc.line(14, y, W - 14, y); y += 8;

    msgs.forEach((m) => {
      if (y > 270) { doc.addPage(); y = 18; }
      doc.setFontSize(10); doc.setTextColor(m.role === "user" ? 30 : 0, 60, m.role === "user" ? 130 : 90);
      doc.setFont(undefined as any, "bold");
      doc.text(m.role === "user" ? "Investigator" : "AI Assistant", 14, y); y += 5;
      doc.setFont(undefined as any, "normal"); doc.setTextColor(40);
      const lines = doc.splitTextToSize(m.content, W - 28);
      doc.text(lines, 14, y); y += lines.length * 5 + 1;
      if (m.sql && m.sql !== "-- no query (informational)" && m.sql !== "-- no matching query") {
        doc.setFontSize(8); doc.setTextColor(120);
        const sq = doc.splitTextToSize("SQL: " + m.sql, W - 28);
        doc.text(sq, 14, y); y += sq.length * 4 + 2;
      }
      y += 3;
    });
    doc.save(`crime-intel-conversation-${convId || "new"}.pdf`);
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "230px 1fr", gap: 16, height: "calc(100vh - 96px)" }}>
      {/* conversation list */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", padding: 12, overflow: "hidden" }}>
        <button className="btn primary" onClick={newConv} style={{ justifyContent: "center", marginBottom: 10 }}>
          <Plus size={15} /> {t("New chat")}
        </button>
        <div style={{ overflowY: "auto", display: "flex", flexDirection: "column", gap: 4 }}>
          {convs.map((c) => (
            <div key={c.id} onClick={() => openConv(c.id)}
              className={`nav-item ${c.id === convId ? "active" : ""}`}
              style={{ justifyContent: "space-between", fontSize: 12, padding: "8px 10px" }}>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {c.title}
              </span>
              <Trash2 size={13} onClick={(e) => removeConv(c.id, e)} className="faint" />
            </div>
          ))}
          {convs.length === 0 && <div className="faint" style={{ fontSize: 12, padding: 8 }}>{t("No conversations yet.")}</div>}
        </div>
      </div>

      {/* chat window */}
      <div className="panel" style={{ display: "flex", flexDirection: "column", padding: 0, overflow: "hidden" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "10px 14px", borderBottom: "1px solid var(--border)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Sparkles size={16} style={{ color: "var(--accent)" }} />
            <span style={{ fontWeight: 600 }}>{t("AI Crime Assistant")}</span>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <select value={lang} onChange={(e) => setLang(e.target.value as any)} style={{ padding: "6px 8px" }}>
              <option value="auto">{t("Auto-detect")}</option>
              <option value="en">English</option>
              <option value="kn">ಕನ್ನಡ Kannada</option>
            </select>
            <button className="btn ghost" onClick={exportPdf} disabled={!msgs.length}>
              <FileDown size={15} /> {t("PDF")}
            </button>
          </div>
        </div>

        <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: 16 }}>
          {msgs.length === 0 && (
            <div className="center" style={{ height: "100%", flexDirection: "column", gap: 18 }}>
              <Sparkles size={34} style={{ color: "var(--accent)" }} />
              <div className="dim" style={{ maxWidth: 460, textAlign: "center", lineHeight: 1.6 }}>
                Ask about FIRs, accused, crime trends, hotspots, offender risk, criminal
                networks, money trails or forecasts — in English or Kannada. Every answer
                includes its evidence trail and generated query.
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", maxWidth: 560 }}>
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="chip accent" style={{ cursor: "pointer" }} onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}
          {msgs.map((m, i) => <Bubble key={i} m={m} onSpeak={speak} canSql={!!user?.permissions.can_view_sql} t={t} />)}
          {busy && <div className="faint" style={{ display: "flex", gap: 8, alignItems: "center", padding: 8 }}>
            <div className="spinner" /> {t("analysing…")}</div>}
        </div>

        <div style={{ borderTop: "1px solid var(--border)", padding: 12 }}>
          {knTyping && (
            <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>
              ಕನ್ನಡ typing on — type in English letters, sends in Kannada:{" "}
              <span style={{ color: "var(--accent)", fontSize: 15 }}>{preview || "ನಮಸ್ಕಾರ"}</span>
            </div>
          )}
          <div style={{ display: "flex", gap: 8 }}>
            <button className="icon-btn" onClick={toggleMic}
              title={t("Voice input")} style={listening ? { borderColor: "var(--red)", color: "var(--red)" } : {}}>
              {listening ? <MicOff size={16} /> : <Mic size={16} />}
            </button>
            <input value={input} onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder={listening ? t("Listening…") : knTyping ? "namaskara, eshtu prakaranagalu…" : t("Ask a question…")}
              style={{ flex: 1 }} />
            <button className="btn primary" onClick={() => send()} disabled={busy || !input.trim()}>
              <Send size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Bubble({ m, onSpeak, canSql, t }:
  { m: Msg; onSpeak: (t: string, l?: string) => void; canSql: boolean; t: (s: string) => string }) {
  const [showEvidence, setShowEvidence] = useState(false);
  const [showSql, setShowSql] = useState(false);
  const [showReason, setShowReason] = useState(false);
  const isUser = m.role === "user";

  return (
    <div style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start", marginBottom: 14 }}>
      <div className="msg" style={{
        maxWidth: "78%", padding: "11px 14px",
        background: isUser ? "var(--accent-2)" : "var(--panel-2)",
        color: isUser ? "#fff" : "var(--text)",
        border: `1px solid ${isUser ? "var(--accent-2)" : "var(--border-strong)"}`,
      }}>
        <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.55 }}>{m.content}</div>

        {m.data?.chart === "bar" && m.data.series?.length > 0 &&
          <div style={{ marginTop: 10 }}><BarViz data={m.data.series} height={200} horizontal /></div>}
        {m.data?.chart === "line" && m.data.series?.length > 0 &&
          <div style={{ marginTop: 10 }}><LineViz data={m.data.series} height={200} area /></div>}
        {m.data?.chart === "table" && m.data.rows?.length > 0 && (
          <div style={{ marginTop: 10, overflowX: "auto" }}>
            <table>
              <thead><tr><th>{t("Name")}</th><th>{t("Risk")}</th><th>{t("Band")}</th><th>{t("Priors")}</th><th>{t("District")}</th></tr></thead>
              <tbody>{m.data.rows.map((r: any, i: number) => (
                <tr key={i}><td>{r.name}</td><td>{r.risk}</td><td>{r.band}</td><td>{r.priors}</td><td>{r.district}</td></tr>
              ))}</tbody>
            </table>
          </div>
        )}

        {!isUser && m.grounding?.status && (
          <div style={{ display: "flex", gap: 8, marginTop: 10, alignItems: "center",
            padding: "6px 10px", border: "1px solid var(--border)", background: "var(--bg)",
            borderLeft: `3px solid ${m.grounding.status === "GROUNDED" ? "var(--green)" : "var(--text-faint)"}` }}>
            <ShieldCheck size={14} style={{ color: m.grounding.status === "GROUNDED" ? "var(--green)" : "var(--text-faint)" }} />
            <div style={{ flex: 1, fontSize: 12 }}>
              <b>{m.grounding.status === "GROUNDED" ? t("Grounded") : t("Not a data claim")}</b>
              {m.grounding.status === "GROUNDED" &&
                <span className="faint"> · {m.grounding.source_count} source(s) · confidence {m.grounding.confidence}</span>}
              <div className="faint" style={{ fontSize: 11 }}>{m.grounding.note}</div>
            </div>
            {m.grounding.provenance && m.grounding.provenance !== "NONE" &&
              <Chip kind={PROV_KIND[m.grounding.provenance]}>{PROV_LABEL[m.grounding.provenance]}</Chip>}
          </div>
        )}

        {!isUser && (
          <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
            {m.intent && <span className="chip">{m.intent}</span>}
            <button className="chip" style={{ cursor: "pointer" }} onClick={() => onSpeak(m.content, m.language)}>
              <Volume2 size={12} /> {t("Speak")}
            </button>
            {m.evidence && m.evidence.length > 0 && (
              <button className="chip" style={{ cursor: "pointer" }} onClick={() => setShowEvidence((v) => !v)}>
                {showEvidence ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                <Database size={12} /> {t("Evidence")} ({m.evidence.length})
              </button>
            )}
            {m.reasoning && m.reasoning.length > 0 && (
              <button className="chip" style={{ cursor: "pointer" }} onClick={() => setShowReason((v) => !v)}>
                <GitBranch size={12} /> {t("Reasoning path")}
              </button>
            )}
            {canSql && m.sql && (
              <button className="chip" style={{ cursor: "pointer" }} onClick={() => setShowSql((v) => !v)}>
                <Code2 size={12} /> {t("SQL")}
              </button>
            )}
          </div>
        )}

        {showEvidence && m.evidence && (
          <div style={{ marginTop: 8, borderTop: "1px solid var(--border)", paddingTop: 8 }}>
            <div className="faint" style={{ fontSize: 11, marginBottom: 4 }}>{t("EVIDENCE TRAIL")}</div>
            {m.evidence.map((e, i) => (
              <div key={i} style={{ fontSize: 12, marginBottom: 4, display: "flex", gap: 6, alignItems: "center" }}>
                <span className="chip" style={{ minWidth: 70, justifyContent: "center" }}>{e.table}</span>
                {e.provenance && <span className={`chip ${PROV_KIND[e.provenance] || ""}`}
                  style={{ fontSize: 10 }}>{PROV_LABEL[e.provenance] || e.provenance}</span>}
                <span className="dim">{e.detail}</span>
              </div>
            ))}
          </div>
        )}
        {showReason && m.reasoning && (
          <div style={{ marginTop: 8, borderTop: "1px solid var(--border)", paddingTop: 10 }}>
            <div className="faint" style={{ fontSize: 11, marginBottom: 8 }}>{t("REASONING PATH")}</div>
            <div style={{ display: "flex", flexWrap: "wrap", alignItems: "stretch", gap: 4 }}>
              {m.reasoning.map((s, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <div style={{ border: "1px solid var(--border-strong)", background: "var(--bg)",
                    padding: "6px 9px", minWidth: 92 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: "var(--accent)" }}>{s.step}</div>
                    <div className="faint" style={{ fontSize: 10, lineHeight: 1.3 }}>{s.detail}</div>
                  </div>
                  {i < m.reasoning!.length - 1 && <ArrowRight size={12} className="faint" />}
                </div>
              ))}
            </div>
          </div>
        )}
        {showSql && (
          <pre className="mono" style={{ marginTop: 8, fontSize: 11, background: "var(--bg)",
            padding: 8, border: "1px solid var(--border)", overflowX: "auto", whiteSpace: "pre-wrap" }}>
            {m.sql}
          </pre>
        )}
      </div>
    </div>
  );
}
