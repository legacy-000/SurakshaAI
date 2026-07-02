import "./globals.css";
import type { Metadata } from "next";
import { AuthProvider } from "../context/auth-context";

export const metadata: Metadata = {
  title: "SURAKSHA AI - Crime Intelligence Platform",
  description: "System for Unified Research, Analytics and Knowledge-based Support for Holistic Analysis - Karnataka Police",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 dark:bg-slate-950">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
