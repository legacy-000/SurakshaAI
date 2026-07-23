import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import {
  LayoutDashboard, MessageSquare, FolderSearch, Share2, UserSearch, Users2,
  TrendingUp, Landmark, Bell, Network, Sun, Moon, LogOut, Shield, BarChart3,
  KeyRound, ScrollText, Command, HelpCircle, Briefcase, HeartPulse, ClipboardCheck, Menu,
} from "lucide-react";
import { useAuth, useTheme, useLang } from "./context";
import { Tour, TOUR_STEPS } from "./Tour";
import Login from "./pages/Login";
import Workspace from "./pages/Workspace";
import CommandCenter from "./pages/CommandCenter";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Cases from "./pages/Cases";
import CaseDetail from "./pages/CaseDetail";
import WorkCase from "./pages/WorkCase";
import NetworkPage from "./pages/NetworkPage";
import Profiling from "./pages/Profiling";
import OffenderDetail from "./pages/OffenderDetail";
import Socio from "./pages/Socio";
import Forecasting from "./pages/Forecasting";
import Financial from "./pages/Financial";
import Patterns from "./pages/Patterns";
import Alerts from "./pages/Alerts";
import MyAccess from "./pages/MyAccess";
import Audit from "./pages/Audit";
import VictimAnalysis from "./pages/VictimAnalysis";
import HotspotDashboard from "./pages/HotspotDashboard";
import CrimeCategoryAnalytics from "./pages/CrimeCategoryAnalytics";
import ApprovalConsole from "./pages/ApprovalConsole";

interface NavDef { to: string; label: string; icon: any; screen: string; section?: string; }
const NAV: NavDef[] = [
  { to: "/", label: "Workspace", icon: LayoutDashboard, screen: "dashboard", section: "Overview" },
  { to: "/command", label: "Command Center", icon: Command, screen: "command" },
  { to: "/chat", label: "AI Assistant", icon: MessageSquare, screen: "chat" },
  { to: "/cases", label: "Cases / FIRs", icon: FolderSearch, screen: "cases", section: "Investigate" },
  { to: "/work", label: "Work a Case", icon: Briefcase, screen: "work" },
  { to: "/network", label: "Criminal Network", icon: Share2, screen: "network" },
  { to: "/profiling", label: "Offender Profiling", icon: UserSearch, screen: "profiling" },
  { to: "/financial", label: "Financial Crime", icon: Landmark, screen: "financial" },
  { to: "/victim-analysis", label: "Victim Analysis", icon: HeartPulse, screen: "victims" },
  { to: "/hotspots", label: "Crime Hotspots", icon: TrendingUp, screen: "patterns", section: "Analyse" },
  { to: "/crime-analytics", label: "Crime Category Analytics", icon: BarChart3, screen: "patterns" },
  { to: "/analytics", label: "Patterns & Trends", icon: Network, screen: "patterns" },
  { to: "/socio", label: "Socio Insights", icon: Users2, screen: "socio" },
  { to: "/forecasting", label: "Forecasting", icon: TrendingUp, screen: "forecasting" },
  { to: "/alerts", label: "Alerts", icon: Bell, screen: "alerts", section: "Monitor" },
  { to: "/access", label: "My Access", icon: KeyRound, screen: "access", section: "Governance" },
  { to: "/approvals", label: "Approval Console", icon: ClipboardCheck, screen: "approvals" },
  { to: "/audit", label: "Audit Trail", icon: ScrollText, screen: "audit" },
];

const TITLES: Record<string, string> = {
  "/": "Workspace", "/command": "Command Center",
  "/chat": "Conversational Crime Intelligence",
  "/cases": "Case & FIR Explorer", "/work": "Work a Case", "/network": "Criminal Network Analysis",
  "/profiling": "Criminology Offender Profiling", "/financial": "Financial Crime & Money Trail",
  "/analytics": "Crime Patterns & Trend Analytics", "/socio": "Sociological Crime Insights",
  "/forecasting": "Crime Forecasting & Early Warning", "/alerts": "Alerts & Early Warning Feed",
  "/victim-analysis": "Victim Analysis & Vulnerability",
  "/hotspots": "Crime Hotspot Dashboard",
  "/crime-analytics": "Crime Category Analytics",
  "/access": "My Access & Permissions", "/approvals": "Approval Console",
  "/audit": "Audit Trail & Accountability",
};

export default function App() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const { lang, setLang, t } = useLang();
  const nav = useNavigate();
  const loc = useLocation();
  const [tourRun, setTourRun] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);

  useEffect(() => {
    if (user && !localStorage.getItem("ci-tour-done")) {
      const t = setTimeout(() => setTourRun(true), 600);
      return () => clearTimeout(t);
    }
  }, [user]);

  useEffect(() => { setMobileNav(false); }, [loc.pathname]);

  if (!user) return <Login />;

  const startTour = () => { nav("/"); setTimeout(() => setTourRun(true), 150); };
  const endTour = () => { setTourRun(false); localStorage.setItem("ci-tour-done", "1"); };

  const allowed = new Set(user.permissions.screens);
  allowed.add("access"); // My Access is available to every role
  const canCommand = ["sho", "pi", "ci", "acp", "dsp", "sp", "dig", "ig", "addl_dgp", "dgp", "commander"].includes(user.role);
  if (canCommand) allowed.add("command");
  const items = NAV.filter((n) => allowed.has(n.screen));
  const tourSteps = TOUR_STEPS.filter((s) => s.selector !== "nav-command" || canCommand);
  const title = TITLES[loc.pathname] ||
    (loc.pathname.startsWith("/cases/") ? "Case Detail" :
      loc.pathname.startsWith("/offender/") ? "Offender Detail" : "Crime Intelligence");

  return (
    <div className="app-shell">
      <Tour steps={tourSteps} run={tourRun} onClose={endTour} />
      <div className={`mobile-overlay ${mobileNav ? "show" : ""}`} onClick={() => setMobileNav(false)} />
      <aside className={`sidebar ${mobileNav ? "mobile-open" : ""}`} data-tour="sidebar">
        <div className="brand">
          <div className="logo">CI</div>
          <div>
            <h1>CRIME INTEL</h1>
            <span>KARNATAKA · LOCAL</span>
          </div>
        </div>
        <nav className="nav">
          {items.map((n) => (
            <div key={n.to}>
              {n.section && <div className="nav-section">{t(n.section)}</div>}
              <button
                className={`nav-item ${loc.pathname === n.to ? "active" : ""}`}
                data-tour={n.screen === "chat" ? "nav-chat" : n.screen === "command" ? "nav-command" : n.screen === "cases" ? "nav-cases" : n.screen === "work" ? "nav-work" : undefined}
                onClick={() => nav(n.to)}>
                <n.icon size={17} />
                {t(n.label)}
              </button>
            </div>
          ))}
        </nav>
        <div style={{ padding: 12, borderTop: "1px solid var(--border)", fontSize: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Shield size={15} className="dim" />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>{user.full_name}</div>
              <div className="faint">{user.rank || user.role}</div>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div style={{ display: "flex", alignItems: "center" }}>
            <button className="mobile-menu-btn" onClick={() => setMobileNav(true)}>
              <Menu size={18} />
            </button>
            <div>
              <h2>{t(title)}</h2>
              <div className="crumb">{user.badge_number} · {user.district}</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }} data-tour="topbar-tools">
            <select value={lang} onChange={(e) => setLang(e.target.value as any)}
              title={t("Language")} style={{ padding: "6px 8px" }}>
              <option value="en">English</option>
              <option value="kn">ಕನ್ನಡ</option>
            </select>
            <button className="icon-btn" onClick={startTour} title={t("Replay guided tour")}>
              <HelpCircle size={16} />
            </button>
            <button className="icon-btn" onClick={toggle} title={t("Toggle theme")}>
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button className="btn ghost" onClick={logout}>
              <LogOut size={15} /> {t("Logout")}
            </button>
          </div>
        </header>
        <div className="content">
          <Routes>
            <Route path="/" element={<Workspace />} />
            <Route path="/command" element={<Guard ok={canCommand}><CommandCenter /></Guard>} />
            <Route path="/analytics-legacy" element={<Dashboard />} />
            <Route path="/chat" element={<Guard ok={allowed.has("chat")}><Chat /></Guard>} />
            <Route path="/cases" element={<Guard ok={allowed.has("cases")}><Cases /></Guard>} />
            <Route path="/work" element={<Guard ok={allowed.has("work")}><WorkCase /></Guard>} />
            <Route path="/cases/:id" element={<Guard ok={allowed.has("cases") || allowed.has("work")}><CaseDetail /></Guard>} />
            <Route path="/network" element={<Guard ok={allowed.has("network")}><NetworkPage /></Guard>} />
            <Route path="/profiling" element={<Guard ok={allowed.has("profiling")}><Profiling /></Guard>} />
            <Route path="/offender/:id" element={<Guard ok={allowed.has("profiling")}><OffenderDetail /></Guard>} />
            <Route path="/financial" element={<Guard ok={allowed.has("financial")}><Financial /></Guard>} />
            <Route path="/hotspots" element={<Guard ok={allowed.has("patterns")}><HotspotDashboard /></Guard>} />
            <Route path="/crime-analytics" element={<Guard ok={allowed.has("patterns")}><CrimeCategoryAnalytics /></Guard>} />
            <Route path="/analytics" element={<Guard ok={allowed.has("patterns")}><Patterns /></Guard>} />
            <Route path="/socio" element={<Guard ok={allowed.has("socio")}><Socio /></Guard>} />
            <Route path="/forecasting" element={<Guard ok={allowed.has("forecasting")}><Forecasting /></Guard>} />
            <Route path="/alerts" element={<Guard ok={allowed.has("alerts")}><Alerts /></Guard>} />
            <Route path="/victim-analysis" element={<Guard ok={allowed.has("victims")}><VictimAnalysis /></Guard>} />
            <Route path="/access" element={<MyAccess />} />
            <Route path="/approvals" element={<Guard ok={allowed.has("approvals")}><ApprovalConsole /></Guard>} />
            <Route path="/audit" element={<Guard ok={allowed.has("audit")}><Audit /></Guard>} />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function Guard({ ok, children }: { ok: boolean; children: any }) {
  const { t } = useLang();
  if (!ok)
    return (
      <div className="panel">
        <div className="panel-title">{t("Access restricted")}</div>
        <p className="dim">Your role does not have permission to view this module.</p>
      </div>
    );
  return children;
}
