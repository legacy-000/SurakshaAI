import { useEffect, useState } from "react";
import { Shield, Sun, Moon } from "lucide-react";
import { api } from "../api";
import { useAuth, useTheme } from "../context";

export default function Login() {
  const { login } = useAuth();
  const { theme, toggle } = useTheme();
  const [users, setUsers] = useState<any[]>([]);
  const [username, setUsername] = useState("dgp");
  const [password, setPassword] = useState("password");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.demoUsers().then(setUsers).catch(() => {}); }, []);

  const submit = async (e?: any) => {
    e?.preventDefault();
    setBusy(true); setErr("");
    try {
      const u = await api.login(username, password);
      login(u);
    } catch {
      setErr("Invalid credentials. Use a demo account below (password: password).");
    } finally { setBusy(false); }
  };

  return (
    <div style={{ height: "100vh", display: "grid", gridTemplateColumns: "1.1fr 1fr" }}>
      {/* left brand panel */}
      <div style={{ background: "var(--bg-2)", borderRight: "1px solid var(--border)",
        padding: 48, display: "flex", flexDirection: "column", justifyContent: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
          <div className="logo" style={{ width: 46, height: 46, background: "var(--accent)",
            color: "#001018", display: "grid", placeItems: "center", fontWeight: 800, fontSize: 18,
            clipPath: "polygon(0 0, 100% 0, 100% 70%, 70% 100%, 0 100%)" }}>CI</div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: 1 }}>CRIME INTELLIGENCE</div>
            <div className="faint" style={{ letterSpacing: 2, fontSize: 12 }}>PLATFORM · KARNATAKA</div>
          </div>
        </div>
        <p className="dim" style={{ maxWidth: 460, lineHeight: 1.7 }}>
          Conversational AI and crime analytics for investigators, analysts and policymakers.
          Query FIRs in natural language, uncover criminal networks, profile offenders,
          trace money trails and forecast emerging crime — all grounded in the case database
          with explainable evidence trails.
        </p>
        <div style={{ display: "flex", gap: 8, marginTop: 24, flexWrap: "wrap" }}>
          {["Natural-language Q&A", "Network analysis", "Offender risk scoring",
            "Money-trail tracing", "Crime forecasting", "Explainable AI"].map((t) => (
            <span key={t} className="chip accent">{t}</span>
          ))}
        </div>
      </div>

      {/* right login */}
      <div style={{ display: "grid", placeItems: "center", position: "relative" }}>
        <button className="icon-btn" onClick={toggle} style={{ position: "absolute", top: 20, right: 20 }}>
          {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
        </button>
        <form className="panel" onSubmit={submit} style={{ width: 380, padding: 28 }}>
          <div className="panel-title"><Shield size={14} /> Secure Sign-in</div>
          <label className="faint" style={{ fontSize: 12 }}>Username</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)}
            style={{ width: "100%", margin: "6px 0 14px" }} />
          <label className="faint" style={{ fontSize: 12 }}>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%", margin: "6px 0 16px" }} />
          {err && <div className="chip Critical" style={{ marginBottom: 12, width: "100%" }}>{err}</div>}
          <button className="btn primary" disabled={busy} style={{ width: "100%", justifyContent: "center" }}>
            {busy ? "Signing in…" : "Sign in"}
          </button>

          <div className="nav-section" style={{ padding: "16px 0 6px" }}>DEMO ACCOUNTS (click to fill)</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 320, overflowY: "auto" }}>
            {users.map((u) => (
              <button type="button" key={u.username} className="btn ghost"
                onClick={() => { setUsername(u.username); setPassword("password"); }}
                style={{ justifyContent: "space-between", fontSize: 11, padding: "6px 10px",
                  background: username === u.username ? "rgba(0,209,255,0.08)" : undefined,
                  borderColor: username === u.username ? "var(--accent)" : undefined }}>
                <span style={{ fontWeight: username === u.username ? 600 : 400 }}>{u.full_name}</span>
                <span className="faint" style={{ fontSize: 10 }}>{u.rank || u.role}</span>
              </button>
            ))}
          </div>
        </form>
      </div>
    </div>
  );
}
