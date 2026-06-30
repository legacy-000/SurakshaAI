import React from "react";

export default function NetworkGraph() {
  return (
    <div className="w-full h-full bg-slate-50 dark:bg-slate-900 border rounded-lg flex items-center justify-center relative overflow-hidden">
      <div className="text-center z-10 glass-panel p-4 rounded-lg">
        <p className="text-sm font-semibold text-primary">React Flow network Graph</p>
        <p className="text-xs text-muted-foreground">Mapping links: Suspect ⇄ case ⇄ Officer</p>
      </div>
      {/* Visual node mocks */}
      <div className="absolute inset-0 flex items-center justify-between px-12 pointer-events-none opacity-40">
        <div className="w-8 h-8 rounded bg-primary text-primary-foreground text-xs flex items-center justify-center font-bold">S</div>
        <div className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground text-xs flex items-center justify-center font-bold">C</div>
        <div className="w-8 h-8 rounded bg-accent text-accent-foreground text-xs flex items-center justify-center font-bold">O</div>
      </div>
    </div>
  );
}
