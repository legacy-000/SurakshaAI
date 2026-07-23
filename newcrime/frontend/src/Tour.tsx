import { useEffect, useLayoutEffect, useState } from "react";
import { X, ArrowRight, ArrowLeft } from "lucide-react";
import { useLang } from "./context";

export interface TourStep {
  selector: string;   // [data-tour="..."]
  title: string;
  body: string;
}

export function Tour({ steps, run, onClose }:
  { steps: TourStep[]; run: boolean; onClose: () => void }) {
  const { t } = useLang();
  const [i, setI] = useState(0);
  const [rect, setRect] = useState<DOMRect | null>(null);

  useEffect(() => { if (run) setI(0); }, [run]);

  useLayoutEffect(() => {
    if (!run) return;
    const measure = () => {
      const el = document.querySelector(`[data-tour="${steps[i]?.selector}"]`);
      if (el) {
        el.scrollIntoView({ block: "center", behavior: "smooth" });
        setRect(el.getBoundingClientRect());
      } else setRect(null);
    };
    measure();
    const tm = setTimeout(measure, 260);
    window.addEventListener("resize", measure);
    return () => { clearTimeout(tm); window.removeEventListener("resize", measure); };
  }, [i, run, steps]);

  if (!run || !steps.length) return null;
  const step = steps[i];
  const pad = 6;
  const box = rect
    ? { top: rect.top - pad, left: rect.left - pad, width: rect.width + pad * 2, height: rect.height + pad * 2 }
    : null;

  // tooltip position: below the highlight, or centered if no target
  const vw = window.innerWidth, vh = window.innerHeight;
  const ttWidth = 320;
  let ttTop = box ? Math.min(box.top + box.height + 12, vh - 200) : vh / 2 - 90;
  let ttLeft = box ? Math.min(Math.max(box.left, 12), vw - ttWidth - 12) : vw / 2 - ttWidth / 2;
  if (box && box.top + box.height + 200 > vh) ttTop = Math.max(box.top - 190, 12);

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 1000 }}>
      {/* dim overlay with a hole around the target */}
      <svg width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
        <defs>
          <mask id="tour-hole">
            <rect width="100%" height="100%" fill="white" />
            {box && <rect x={box.left} y={box.top} width={box.width} height={box.height} fill="black" />}
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="rgba(3,7,15,0.72)" mask="url(#tour-hole)" />
        {box && <rect x={box.left} y={box.top} width={box.width} height={box.height}
          fill="none" stroke="var(--accent)" strokeWidth={2} />}
      </svg>

      {/* tooltip */}
      <div style={{
        position: "absolute", top: ttTop, left: ttLeft, width: ttWidth,
        background: "var(--panel)", border: "1px solid var(--accent)",
        padding: 16, boxShadow: "var(--shadow)",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <span className="faint" style={{ fontSize: 11, letterSpacing: 1 }}>
            {t("STEP")} {i + 1} / {steps.length}
          </span>
          <X size={16} style={{ cursor: "pointer" }} className="faint" onClick={onClose} />
        </div>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 6 }}>{t(step.title)}</div>
        <div className="dim" style={{ fontSize: 13, lineHeight: 1.55, marginBottom: 14 }}>{t(step.body)}</div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <button className="btn ghost" onClick={onClose} style={{ fontSize: 12 }}>{t("Skip tour")}</button>
          <div style={{ display: "flex", gap: 8 }}>
            {i > 0 && <button className="btn" onClick={() => setI(i - 1)}><ArrowLeft size={14} /> {t("Back")}</button>}
            {i < steps.length - 1
              ? <button className="btn primary" onClick={() => setI(i + 1)}>{t("Next")} <ArrowRight size={14} /></button>
              : <button className="btn primary" onClick={onClose}>{t("Finish")}</button>}
          </div>
        </div>
      </div>
    </div>
  );
}

export const TOUR_STEPS: TourStep[] = [
  { selector: "sidebar", title: "Navigation",
    body: "Modules are grouped by workflow — Overview, Investigate, Analyse, Monitor and Governance. Your role decides what you see." },
  { selector: "workspace-kpis", title: "Your Workspace",
    body: "Your personal home. These KPIs are scoped to your role and jurisdiction — an investigator sees their caseload, a DSP sees the district." },
  { selector: "nav-chat", title: "AI Assistant",
    body: "Ask about FIRs, offenders, networks, money trails or forecasts in plain English or Kannada. Every answer is grounded with an evidence trail and reasoning path." },
  { selector: "nav-command", title: "Command Center",
    body: "Senior officers get a strategic view: a live Karnataka hotspot map, intelligence stream, priority alerts and the offender pool." },
  { selector: "nav-cases", title: "Cases / FIR Explorer",
    body: "Browse all cases, filter by crime type, district, or status." },
  { selector: "nav-work", title: "Work a Case",
    body: "Click 'Start Investigation' to open the investigation dashboard." },
  { selector: "nav-evidence", title: "Evidence Tab",
    body: "Upload and manage case evidence with AI-generated summaries." },
  { selector: "nav-ai-assistant", title: "Case AI Assistant",
    body: "Ask questions about cases, suspects, and crime patterns." },
  { selector: "topbar-tools", title: "Theme, tour & sign-out",
    body: "Toggle dark/light, replay this tour anytime with the ? button, and sign out. That's it — start exploring!" },
];
