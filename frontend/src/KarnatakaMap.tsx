import { useMemo, useState } from "react";

export interface DistrictPoint {
  district: string; count: number; lat: number; lon: number;
  loss?: number; top_crime?: string; in_scope?: boolean;
}

// Approximate Karnataka state boundary (lat, lon), clockwise. Stylised — the
// bubbles use real case centroids and are projected with the same transform,
// so they sit in the right place on the state.
const OUTLINE: [number, number][] = [
  [18.4, 77.5], [17.9, 77.1], [17.4, 76.9], [16.9, 77.6], [16.2, 77.4],
  [15.6, 77.3], [15.1, 77.0], [14.5, 76.9], [13.9, 77.6], [13.4, 78.2],
  [12.8, 78.2], [12.3, 77.5], [11.9, 76.9], [12.0, 76.1], [12.4, 75.4],
  [12.87, 74.85], [13.5, 74.7], [14.3, 74.3], [14.9, 74.1], [15.5, 74.2],
  [16.2, 74.5], [16.9, 74.6], [17.4, 76.0], [17.9, 76.9],
];

const LAT = { min: 11.6, max: 18.6 };
const LON = { min: 73.9, max: 78.5 };

function heat(t: number) {
  // 0..1 -> green→amber→red
  if (t < 0.5) return `rgb(${Math.round(36 + t * 2 * 219)}, ${Math.round(209 - t * 2 * 33)}, ${Math.round(139 - t * 2 * 107)})`;
  const u = (t - 0.5) * 2;
  return `rgb(255, ${Math.round(176 - u * 99)}, ${Math.round(32 + u * 62)})`;
}

export function KarnatakaMap({ districts, selected, onSelect, height = 460 }:
  { districts: DistrictPoint[]; selected?: string | null;
    onSelect?: (d: string | null) => void; height?: number }) {
  const [hover, setHover] = useState<string | null>(null);
  const W = 620, H = 560;

  const proj = (lat: number, lon: number): [number, number] => [
    ((lon - LON.min) / (LON.max - LON.min)) * W,
    ((LAT.max - lat) / (LAT.max - LAT.min)) * H,
  ];

  const outlinePath = useMemo(() => {
    const pts = OUTLINE.map(([la, lo]) => proj(la, lo));
    return "M " + pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" L ") + " Z";
  }, []);

  const max = Math.max(1, ...districts.map((d) => d.count));

  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", maxWidth: 560, height, background: "var(--bg)", border: "1px solid var(--border)" }}
        className="graph-bg">
        <path d={outlinePath} fill="var(--panel-2)" stroke="var(--border-strong)" strokeWidth={1.5} opacity={0.75} />
        {districts.map((d) => {
          if (d.lat == null || d.lon == null) return null;
          const [x, y] = proj(d.lat, d.lon);
          const t = d.count / max;
          const r = 7 + t * 20;
          const active = hover === d.district || selected === d.district;
          const dim = selected && selected !== d.district;
          return (
            <g key={d.district} transform={`translate(${x},${y})`} style={{ cursor: "pointer" }}
              onMouseEnter={() => setHover(d.district)} onMouseLeave={() => setHover(null)}
              onClick={() => onSelect?.(selected === d.district ? null : d.district)}
              opacity={dim ? 0.35 : 1}>
              <circle r={r} fill={heat(t)} fillOpacity={0.35} stroke={heat(t)} strokeWidth={active ? 2.5 : 1.5} />
              <circle r={3} fill={heat(t)} />
              {(active || r > 16) && (
                <text y={-r - 4} textAnchor="middle" fontSize={11} fill="var(--text)"
                  style={{ pointerEvents: "none", fontWeight: active ? 700 : 400 }}>
                  {d.district} ({d.count})
                </text>
              )}
            </g>
          );
        })}
      </svg>

      {/* legend + selected detail */}
      <div style={{ flex: 1, minWidth: 180 }}>
        <div className="faint" style={{ fontSize: 11, marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.6 }}>
          Incident density
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
          <div style={{ height: 10, flex: 1, background: "linear-gradient(90deg, rgb(36,209,139), rgb(255,176,32), rgb(255,77,94))" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11 }} className="faint">
          <span>Low</span><span>High ({max})</span>
        </div>

        <div style={{ marginTop: 16 }}>
          <div className="faint" style={{ fontSize: 11, marginBottom: 6, textTransform: "uppercase", letterSpacing: 0.6 }}>
            {selected ? "Selected district" : "Top hotspots"}
          </div>
          {(selected
            ? districts.filter((d) => d.district === selected)
            : [...districts].sort((a, b) => b.count - a.count).slice(0, 6)
          ).map((d) => (
            <div key={d.district} onClick={() => onSelect?.(selected === d.district ? null : d.district)}
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "6px 8px", cursor: "pointer", fontSize: 13,
                background: selected === d.district ? "var(--panel-2)" : "transparent",
                borderBottom: "1px solid var(--border)" }}>
              <span>{d.district}</span>
              <span className="dim">{d.count} · {d.top_crime}</span>
            </div>
          ))}
          {selected && (
            <button className="btn ghost" style={{ marginTop: 10, fontSize: 12 }}
              onClick={() => onSelect?.(null)}>Clear selection</button>
          )}
        </div>
      </div>
    </div>
  );
}
