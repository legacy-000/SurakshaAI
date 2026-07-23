import { Check, X, Shield, Eye, EyeOff, Code2, FileDown, ScrollText } from "lucide-react";
import { useAuth, useLang } from "../context";
import { Chip, Panel } from "../components";

const SCREEN_LABELS: Record<string, string> = {
  dashboard: "Command Dashboard", chat: "AI Assistant", cases: "Cases / FIRs",
  network: "Criminal Network", profiling: "Offender Profiling", financial: "Financial Crime",
  patterns: "Patterns & Trends", socio: "Socio Insights", forecasting: "Forecasting",
  alerts: "Alerts", audit: "Audit Trail",
};

const ALL_SCREENS = ["dashboard", "chat", "cases", "network", "profiling", "financial",
  "patterns", "socio", "forecasting", "alerts", "audit"];

export default function MyAccess() {
  const { user } = useAuth();
  const { t } = useLang();
  if (!user) return null;
  const p = user.permissions;
  const has = (s: string) => p.screens.includes(s);

  const caps = [
    { label: t("View unmasked PII"), on: p.can_view_pii, icon: p.can_view_pii ? Eye : EyeOff,
      desc: "See victim/accused names, phone numbers and addresses in the clear." },
    { label: t("View generated SQL"), on: p.can_view_sql, icon: Code2,
      desc: "Inspect the query behind every AI answer." },
    { label: t("Export / PDF"), on: p.can_export, icon: FileDown,
      desc: "Download reports and conversation transcripts." },
    { label: t("View audit trail"), on: p.can_view_audit, icon: ScrollText,
      desc: "Review who accessed which records, and when." },
  ];

  return (
    <div className="grid" style={{ gap: 16 }}>
      <Panel title={<span><Shield size={13} /> {t("Your Profile & Authority")}</span> as any}>
        <div className="grid cols-4">
          <Field label={t("Officer")} value={user.full_name} />
          <Field label={t("Rank")} value={user.rank} />
          <Field label={t("Badge No.")} value={user.badge_number} />
          <Field label={t("Jurisdiction")} value={user.district} />
        </div>
        <div style={{ marginTop: 12 }}>
          <Chip kind="accent">{t("Data scope:")} {p.scope}</Chip>
        </div>
        <div className="dim" style={{ fontSize: 12, marginTop: 12, lineHeight: 1.6 }}>
          Access is enforced by the backend on every request — screens are gated, PII is masked
          for roles without clearance, and every access is written to the audit trail. This mirrors
          the Karnataka Police role hierarchy (Constable → Sub-Inspector → SHO → DSP → Commander,
          plus Analyst).
        </div>
      </Panel>

      <div className="grid cols-2">
        <Panel title={t("Capabilities")}>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {caps.map((c) => (
              <div key={c.label} style={{ display: "flex", gap: 10, alignItems: "start",
                padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                <c.icon size={16} className={c.on ? "" : "faint"}
                  style={{ marginTop: 2, color: c.on ? "var(--green)" : "var(--text-faint)" }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{c.label}</div>
                  <div className="faint" style={{ fontSize: 12 }}>{c.desc}</div>
                </div>
                {c.on ? <Chip kind="green">{t("Granted")}</Chip> : <Chip kind="Critical">{t("Denied")}</Chip>}
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={t("Screen Access Matrix")}>
          <table>
            <thead><tr><th>{t("Module")}</th><th style={{ textAlign: "right" }}>{t("Access")}</th></tr></thead>
            <tbody>
              {ALL_SCREENS.map((s) => (
                <tr key={s}>
                  <td>{t(SCREEN_LABELS[s])}</td>
                  <td style={{ textAlign: "right" }}>
                    {has(s)
                      ? <Check size={16} style={{ color: "var(--green)" }} />
                      : <X size={16} style={{ color: "var(--text-faint)" }} />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="faint" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontWeight: 600, marginTop: 4 }}>{value}</div>
    </div>
  );
}
