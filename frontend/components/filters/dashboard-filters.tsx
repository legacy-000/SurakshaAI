import React from "react";

export default function DashboardFilters() {
  return (
    <div className="flex gap-4 p-4 bg-slate-50 dark:bg-slate-900 border rounded-lg">
      <select className="bg-background border rounded px-3 py-1.5 text-sm">
        <option>All Crime Types</option>
        <option>Theft</option>
        <option>Assault</option>
        <option>Cyber Crime</option>
      </select>
      <input 
        type="date" 
        className="bg-background border rounded px-3 py-1.5 text-sm" 
      />
    </div>
  );
}
