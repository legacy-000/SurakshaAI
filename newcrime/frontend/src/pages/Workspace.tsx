import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MessageSquare, FolderSearch, Bell, Command, ArrowRight, Clock } from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { Chip, Loading, Panel, Stat } from "../components";

export default function Workspace() {
  const { user } = useAuth();
  const { t } = useLang();
  const nav = useNavigate();
  const [d, setD] = useState<any>(null);

  useEffect(() => { api.workspace().then(setD); }, []);
  if (!d) return <Loading label="Loading your workspace…" />;

  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 }}>
        <div>
          <h2 style={{ margin: 0 }}>{t(greet)}, {d.officer.name}</h2>
          <div className="faint" style={{ fontSize: 13 }}>
            {d.officer.rank} · {d.officer.district} · <span style={{ textTransform: "capitalize" }}>{d.officer.scope} {t("scope")}</span>
          </div>
        </div>
        {d.can_command &&
          <button className="btn primary" onClick={() => nav("/command")} data-tour="nav-command-btn">
            <Command size={15} /> {t("Open Command Center")}
          </button>}
      </div>

      <div className="grid cols-4" data-tour="workspace-kpis">
        {d.kpis.map((k: any, i: number) => (
          <Stat key={i} label={t(k.label)} value={k.value} color={k.accent} />
        ))}
      </div>

      {/* quick actions */}
      <div className="grid cols-4">
        {[
          { label: "Ask the AI", icon: MessageSquare, to: "/chat", screen: "chat" },
          { label: "Search cases", icon: FolderSearch, to: "/cases", screen: "cases" },
          { label: "View alerts", icon: Bell, to: "/alerts", screen: "alerts" },
          { label: "Command Center", icon: Command, to: "/command", screen: "command", command: true },
        ].filter((a) => a.command ? d.can_command : user?.permissions.screens.includes(a.screen))
          .map((a) => (
            <button key={a.label} className="card" onClick={() => nav(a.to)}
              style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer", textAlign: "left", color: "var(--text)" }}>
              <a.icon size={18} style={{ color: "var(--accent)" }} />
              <span style={{ flex: 1, fontWeight: 600 }}>{t(a.label)}</span>
              <ArrowRight size={15} className="faint" />
            </button>
          ))}
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1fr 2fr" }}>
        <Panel title={t("Cases in your jurisdiction")} className=""
          info={{ what: "Recent cases within your role's data scope.", data: "cases table, scoped by district", brief: "Role-based access (#10)" }}
          right={user?.permissions.screens.includes("cases") &&
            <button className="btn ghost" onClick={() => nav("/cases")}>All <ArrowRight size={13} /></button>}>
          <div style={{ maxHeight: 300, overflowY: "auto" }}>
            {d.my_cases.length === 0 && <div className="faint">No cases in scope.</div>}
            {d.my_cases.map((c: any) => (
              <div key={c.id} onClick={() => user?.permissions.screens.includes("cases") && nav(`/cases/${c.id}`)}
                style={{ padding: "9px 0", borderBottom: "1px solid var(--border)",
                  cursor: user?.permissions.screens.includes("cases") ? "pointer" : "default" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{c.title}</span>
                  <Chip kind={c.severity}>{c.severity}</Chip>
                </div>
                <div className="faint mono" style={{ fontSize: 11 }}>{c.fir_number} · {c.crime_type} · {c.status}</div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title={t("Intelligence stream")}
          info={{ what: "Latest investigation events in your jurisdiction — FIRs, arrests, evidence, chargesheets.", data: "timeline_events joined to cases" }}>
          <div style={{ maxHeight: 300, overflowY: "auto" }}>
            {d.stream.map((e: any, i: number) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "9px 0", borderBottom: "1px solid var(--border)" }}>
                <Clock size={14} className="faint" style={{ marginTop: 2 }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13 }}>
                    <b>{e.title}</b> <Chip>{e.type}</Chip>
                  </div>
                  <div className="faint" style={{ fontSize: 11 }}>
                    {e.case} · {e.district} · {e.time?.slice(0, 10)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
