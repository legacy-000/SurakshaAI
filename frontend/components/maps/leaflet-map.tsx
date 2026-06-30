import React from "react";

export default function LeafletMap() {
  return (
    <div className="w-full h-full bg-slate-100 dark:bg-slate-900 border rounded-lg flex items-center justify-center relative overflow-hidden">
      <div className="text-center space-y-2 z-10 p-6 glass-panel rounded-xl">
        <p className="text-sm font-semibold text-primary">Leaflet GIS Mapping Layer</p>
        <p className="text-xs text-muted-foreground">Showing active hotspots across Bangalore (SRID: 4326)</p>
      </div>
      {/* Background simulated tile grid */}
      <div className="absolute inset-0 opacity-20 grid grid-cols-6 grid-rows-6 pointer-events-none">
        {Array.from({ length: 36 }).map((_, i) => (
          <div key={i} className="border border-slate-300 dark:border-slate-700"></div>
        ))}
      </div>
    </div>
  );
}
