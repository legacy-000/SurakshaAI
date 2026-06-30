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
    const savedToken = localStorage.getItem("suraksha_token");
    if (savedToken) {
      setToken(savedToken);
      // Mock loading profile
      setUser({ role: "officer", name: "Officer" });
    }
  }, []);

  const login = (token: string, user: any) => {
    localStorage.setItem("suraksha_token", token);
    setToken(token);
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem("suraksha_token");
    setToken(null);
    setUser(null);
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export default AuthContext;
