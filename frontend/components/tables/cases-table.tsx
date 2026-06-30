import React from "react";

export default function CasesTable() {
  return (
    <div className="overflow-x-auto w-full">
      <table className="min-w-full divide-y divide-border">
        <thead>
          <tr className="bg-slate-50 dark:bg-slate-900 text-left text-xs font-semibold text-muted-foreground uppercase">
            <th className="px-6 py-3">FIR Number</th>
            <th className="px-6 py-3">Title</th>
            <th className="px-6 py-3">Crime Type</th>
            <th className="px-6 py-3">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border text-sm">
          <tr>
            <td className="px-6 py-4 font-medium">FIR-2026-0812</td>
            <td className="px-6 py-4">Commercial burglary at MG Road</td>
            <td className="px-6 py-4">Theft</td>
            <td className="px-6 py-4">
              <span className="px-2 py-1 text-xs font-semibold rounded bg-amber-100 text-amber-800">
                Active
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
