import React from "react";

export default function Sidebar() {
  return (
    <aside className="w-64 border-r bg-card flex flex-col h-full">
      <div className="p-6 border-b">
        <h2 className="font-bold text-lg text-primary">Intelligence Command</h2>
      </div>

      <nav className="flex-1 p-4 space-y-2">
        <a href="#" className="block p-3 rounded-lg bg-accent text-accent-foreground font-medium">
          Dashboard
        </a>
        <a href="#" className="block p-3 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-muted-foreground transition">
          Spatial Hotspots
        </a>
        <a href="#" className="block p-3 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-muted-foreground transition">
          Link Network
        </a>
        <a href="#" className="block p-3 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-muted-foreground transition">
          Forecasting
        </a>
        <a href="#" className="block p-3 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-muted-foreground transition">
          RAG Chatbot
        </a>
      </nav>

      <div className="p-4 border-t text-xs text-muted-foreground">
        Version 0.1.0 (Scaffolding)
      </div>
    </aside>
  );
}
