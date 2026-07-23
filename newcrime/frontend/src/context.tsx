import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { translate } from "./i18n";

/* ── Language (global) ─────────────────────────────────────────────── */
type Lang = "en" | "kn";
const LangCtx = createContext<{ lang: Lang; setLang: (l: Lang) => void; t: (s: string) => string }>({
  lang: "en", setLang: () => {}, t: (s) => s,
});

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(
    () => (localStorage.getItem("ci-lang") as Lang) || "en"
  );
  const setLang = (l: Lang) => { setLangState(l); localStorage.setItem("ci-lang", l); };
  const t = (s: string) => translate(lang, s);
  return <LangCtx.Provider value={{ lang, setLang, t }}>{children}</LangCtx.Provider>;
}
export const useLang = () => useContext(LangCtx);

/* ── Theme ─────────────────────────────────────────────────────────── */
type Theme = "dark" | "light";
const ThemeCtx = createContext<{ theme: Theme; toggle: () => void }>({
  theme: "dark",
  toggle: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem("ci-theme") as Theme) || "dark"
  );
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("ci-theme", theme);
  }, [theme]);
  return (
    <ThemeCtx.Provider value={{ theme, toggle: () => setTheme((t) => (t === "dark" ? "light" : "dark")) }}>
      {children}
    </ThemeCtx.Provider>
  );
}
export const useTheme = () => useContext(ThemeCtx);

/* ── Auth ──────────────────────────────────────────────────────────── */
export interface User {
  id: number;
  username: string;
  full_name: string;
  role: string;
  rank: string;
  badge_number: string;
  district: string;
  subdivision?: string;
  range_name?: string;
  station?: string;
  permissions: {
    screens: string[];
    can_view_pii: boolean;
    can_view_sql: boolean;
    can_export: boolean;
    can_view_audit: boolean;
    can_investigate: boolean;
    scope: string;
    command_level?: string | null;
  };
}

const AuthCtx = createContext<{
  user: User | null;
  login: (u: User) => void;
  logout: () => void;
}>({ user: null, login: () => {}, logout: () => {} });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const s = localStorage.getItem("ci-user");
    return s ? JSON.parse(s) : null;
  });
  const login = (u: User) => {
    setUser(u);
    localStorage.setItem("ci-user", JSON.stringify(u));
  };
  const logout = () => {
    setUser(null);
    localStorage.removeItem("ci-user");
  };
  return <AuthCtx.Provider value={{ user, login, logout }}>{children}</AuthCtx.Provider>;
}
export const useAuth = () => useContext(AuthCtx);
