import React from "react";

export default function CaseDetailsDialog() {
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-card w-full max-w-lg p-6 rounded-xl border space-y-4">
        <h3 className="text-lg font-semibold text-primary">Case Detailed Report Summary</h3>
        <p className="text-sm text-muted-foreground">
          Showing structural overlay details dialog...
        </p>
        <div className="flex justify-end">
          <button className="px-4 py-2 bg-primary text-primary-foreground rounded text-sm font-medium">
            Close View
          </button>
        </div>
      </div>
    </div>
  );
}
