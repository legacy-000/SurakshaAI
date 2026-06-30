import React from "react";
import Sidebar from "../components/sidebar/sidebar";
import Navbar from "../components/navbar/navbar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-y-auto">
        <Navbar />
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
