import { useEffect, useMemo, useRef, useState } from "react";

export interface GNode {
  id: number;
  label: string;
  color?: string;
  size?: number;
  meta?: string;
}
export interface GEdge {
  source: number;
  target: number;
  color?: string;
  width?: number;
  label?: string;
}

interface Sim { id: number; x: number; y: number; vx: number; vy: number; }

/** Lightweight force-directed graph rendered as SVG. No external dependency. */
export function NetworkGraph({
  nodes, edges, height = 480, onNodeClick,
}: {
  nodes: GNode[]; edges: GEdge[]; height?: number;
  onNodeClick?: (id: number) => void;
}) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);
  const [, force] = useState(0);
  const simRef = useRef<Map<number, Sim>>(new Map());
  const [hover, setHover] = useState<number | null>(null);
  const dragRef = useRef<number | null>(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setWidth(el.clientWidth));
    ro.observe(el);
    setWidth(el.clientWidth);
    return () => ro.disconnect();
  }, []);

  // init positions
  useMemo(() => {
    const m = new Map<number, Sim>();
    nodes.forEach((n, i) => {
      const prev = simRef.current.get(n.id);
      const ang = (i / Math.max(nodes.length, 1)) * Math.PI * 2;
      m.set(n.id, prev || {
        id: n.id,
        x: width / 2 + Math.cos(ang) * 140 + (Math.random() - 0.5) * 40,
        y: height / 2 + Math.sin(ang) * 140 + (Math.random() - 0.5) * 40,
        vx: 0, vy: 0,
      });
    });
    simRef.current = m;
  }, [nodes]);

  // physics loop
  useEffect(() => {
    if (!nodes.length) return;
    let raf = 0;
    let ticks = 0;
    const adj = edges.map((e) => [e.source, e.target] as const);
    const step = () => {
      const sim = simRef.current;
      const arr = [...sim.values()];
      // repulsion
      for (let i = 0; i < arr.length; i++) {
        for (let jx = i + 1; jx < arr.length; jx++) {
          const a = arr[i], b = arr[jx];
          let dx = a.x - b.x, dy = a.y - b.y;
          let d2 = dx * dx + dy * dy || 0.01;
          const f = 2400 / d2;
          const d = Math.sqrt(d2);
          const ux = dx / d, uy = dy / d;
          a.vx += ux * f; a.vy += uy * f;
          b.vx -= ux * f; b.vy -= uy * f;
        }
      }
      // springs
      for (const [s, t] of adj) {
        const a = sim.get(s), b = sim.get(t);
        if (!a || !b) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
        const f = (d - 90) * 0.02;
        const ux = dx / d, uy = dy / d;
        a.vx += ux * f; a.vy += uy * f;
        b.vx -= ux * f; b.vy -= uy * f;
      }
      // centering + integrate
      for (const n of arr) {
        n.vx += (width / 2 - n.x) * 0.002;
        n.vy += (height / 2 - n.y) * 0.002;
        n.vx *= 0.82; n.vy *= 0.82;
        if (dragRef.current !== n.id) { n.x += n.vx; n.y += n.vy; }
        n.x = Math.max(24, Math.min(width - 24, n.x));
        n.y = Math.max(24, Math.min(height - 24, n.y));
      }
      force((v) => v + 1);
      ticks++;
      if (ticks < 320) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [nodes, edges, width, height]);

  const sim = simRef.current;
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  const onMove = (e: React.MouseEvent) => {
    if (dragRef.current == null) return;
    const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
    const s = sim.get(dragRef.current);
    if (s) { s.x = e.clientX - rect.left; s.y = e.clientY - rect.top; s.vx = 0; s.vy = 0; }
    force((v) => v + 1);
  };

  if (!nodes.length)
    return <div className="center faint" style={{ height }}>No network data for the current filter.</div>;

  return (
    <div ref={wrapRef} style={{ width: "100%" }}>
      <svg
        className="graph-bg"
        width={width} height={height}
        style={{ border: "1px solid var(--border)", background: "var(--bg)", cursor: dragRef.current != null ? "grabbing" : "default" }}
        onMouseMove={onMove}
        onMouseUp={() => (dragRef.current = null)}
        onMouseLeave={() => (dragRef.current = null)}
      >
        {edges.map((e, i) => {
          const a = sim.get(e.source), b = sim.get(e.target);
          if (!a || !b) return null;
          const active = hover === e.source || hover === e.target;
          return (
            <line key={i} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={e.color || "var(--border-strong)"}
              strokeWidth={active ? (e.width || 1) + 1 : e.width || 1}
              strokeOpacity={hover == null ? 0.5 : active ? 0.95 : 0.12} />
          );
        })}
        {nodes.map((n) => {
          const s = sim.get(n.id);
          if (!s) return null;
          const r = n.size || 9;
          const active = hover === n.id;
          return (
            <g key={n.id}
              transform={`translate(${s.x},${s.y})`}
              style={{ cursor: "pointer" }}
              onMouseDown={() => (dragRef.current = n.id)}
              onMouseEnter={() => setHover(n.id)}
              onMouseLeave={() => setHover(null)}
              onClick={() => onNodeClick?.(n.id)}>
              <circle r={active ? r + 2 : r} fill={n.color || "#00d1ff"}
                stroke="var(--bg)" strokeWidth={1.5}
                opacity={hover == null || active ? 1 : 0.35} />
              {(active || nodes.length <= 40) && (
                <text x={r + 4} y={4} fontSize={11} fill="var(--text)"
                  style={{ pointerEvents: "none", opacity: hover == null || active ? 1 : 0.4 }}>
                  {n.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      {hover != null && nodeMap.get(hover)?.meta && (
        <div className="faint" style={{ fontSize: 12, marginTop: 6 }}>
          {nodeMap.get(hover)!.label} — {nodeMap.get(hover)!.meta}
        </div>
      )}
    </div>
  );
}
