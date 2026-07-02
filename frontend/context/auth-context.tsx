"use client";

import React, { createContext, useState, useEffect } from "react";

interface AuthContextType {
  token: string | null;
  user: any | null;
  isAuthenticated: boolean;
  login: (token: string, user: any) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any | null>(null);

  useEffect(() => {
    // Support both legacy and Catalyst tokens
    const savedToken = localStorage.getItem("catalyst_auth_token") || localStorage.getItem("suraksha_token");
    if (savedToken) {
      setToken(savedToken);
      // Mock loading profile (In production, fetch from Catalyst Auth)
      setUser({ role: "officer", name: "Officer" });
    }
  }, []);

  const login = (newToken: string, userData: any) => {
    localStorage.setItem("catalyst_auth_token", newToken);
    setToken(newToken);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("catalyst_auth_token");
    localStorage.removeItem("suraksha_token");
    setToken(null);
    setUser(null);
    // Redirect to Catalyst logout if in production
    if (process.env.NEXT_PUBLIC_CATALYST_ENV === "production") {
      window.location.href = "/auth/logout";
    }
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
