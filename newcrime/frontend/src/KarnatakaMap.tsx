import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

export interface DistrictPoint {
  district: string; count: number; lat: number; lon: number;
  loss?: number; top_crime?: string; in_scope?: boolean;
}

// Karnataka's bounding box — used to frame the map on load.
const KA_BOUNDS = L.latLngBounds([11.55, 74.0], [18.5, 78.6]);

function heat(t: number) {
  // 0..1 -> green→amber→red
  if (t < 0.5) {
    return `rgb(${Math.round(36 + t * 2 * 219)}, ${Math.round(209 - t * 2 * 33)}, ${Math.round(139 - t * 2 * 107)})`;
  }
  const u = (t - 0.5) * 2;
  return `rgb(255, ${Math.round(176 - u * 99)}, ${Math.round(32 + u * 62)})`;
}

export function KarnatakaMap({ districts, selected, onSelect, height = 460 }:
  { districts: DistrictPoint[]; selected?: string | null;
    onSelect?: (d: string | null) => void; height?: number }) {
  const elRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const [ready, setReady] = useState(false);

  const max = Math.max(1, ...districts.map((d) => d.count));

  useEffect(() => {
    if (!elRef.current || mapRef.current) return;
    const map = L.map(elRef.current, {
      zoomControl: true,
      attributionControl: true,
      scrollWheelZoom: false, // don't hijack page scroll
    });
    // Carto dark basemap — matches the dark UI and needs no API key.
    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        subdomains: "abcd",
        maxZoom: 19,
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      },
    ).addTo(map);
    map.fitBounds(KA_BOUNDS, { padding: [10, 10] });
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    setReady(true);
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  // redraw markers whenever the data or selection changes
  useEffect(() => {
    const layer = layerRef.current;
    if (!ready || !layer) return;
    layer.clearLayers();

    districts.forEach((d) => {
      if (d.lat == null || d.lon == null) return;
      const t = d.count / max;
      const colour = heat(t);
      const dim = selected && selected !== d.district;

      const marker = L.circleMarker([d.lat, d.lon], {
        radius: 8 + t * 18,
        color: colour,
        weight: selected === d.district ? 3 : 1.5,
        fillColor: colour,
        fillOpacity: dim ? 0.12 : 0.35,
        opacity: dim ? 0.3 : 1,
      });

      marker.bindTooltip(
        `<b>${d.district}</b><br/>${d.count} cases` +
        (d.top_crime ? `<br/>Top: ${d.top_crime}` : ""),
        { direction: "top", offset: [0, -6] },
      );
      marker.on("click", () => onSelect?.(selected === d.district ? null : d.district));
      marker.addTo(layer);

      // permanent name label so districts are identifiable without hovering
      L.marker([d.lat, d.lon], {
        interactive: false,
        icon: L.divIcon({
          className: "ka-map-label",
          html: `<span>${d.district} (${d.count})</span>`,
          iconSize: [0, 0],
        }),
      }).addTo(layer);
    });
  }, [districts, selected, ready, max, onSelect]);

  return (
    <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
      <div style={{ flex: "1 1 380px", minWidth: 300 }}>
        <div ref={elRef}
          style={{ height, width: "100%", border: "1px solid var(--border)",
                   background: "var(--bg)" }} />
      </div>

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
