import { ReactNode, useState } from "react";
import { Info } from "lucide-react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis,
  Tooltip, ResponsiveContainer, CartesianGrid, AreaChart, Area,
} from "recharts";

export interface InfoMeta { what: string; data?: string; brief?: string; }

export function InfoDot({ info }: { info: InfoMeta }) {
  const [open, setOpen] = useState(false);
  return (
    <span style={{ position: "relative", display: "inline-flex" }}
      onMouseEnter={() => setOpen(true)} onMouseLeave={() => setOpen(false)}>
      <Info size={14} className="faint" style={{ cursor: "help" }} onClick={() => setOpen((v) => !v)} />
      {open && (
        <span style={{
          position: "absolute", top: 20, left: 0, zIndex: 50, width: 260,
          background: "var(--panel-2)", border: "1px solid var(--border-strong)",
          padding: "10px 12px", boxShadow: "var(--shadow)", fontSize: 12,
          lineHeight: 1.5, color: "var(--text)", textTransform: "none",
          letterSpacing: "normal", fontWeight: 400,
        }}>
          <div>{info.what}</div>
          {info.data && <div className="faint" style={{ marginTop: 6 }}><b>Data:</b> {info.data}</div>}
          {info.brief && <div style={{ marginTop: 6, color: "var(--accent)" }}>✓ Brief: {info.brief}</div>}
        </span>
      )}
    </span>
  );
}

export const COLORS = ["#00d1ff", "#2f81f7", "#ffb020", "#24d18b", "#a06bff",
  "#ff4d5e", "#ff8a4d", "#4dd0e1", "#c471ed", "#f76b8a"];

export function Panel({ title, children, right, className = "", info }:
  { title?: ReactNode; children: ReactNode; right?: ReactNode; className?: string; info?: InfoMeta }) {
  return (
    <div className={`panel ${className}`}>
      {title && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div className="panel-title" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {title}{info && <InfoDot info={info} />}
          </div>
          {right}
        </div>
      )}
      {children}
    </div>
  );
}

export function Stat({ label, value, sub, color }:
  { label: string; value: ReactNode; sub?: string; color?: string }) {
  return (
    <div className="stat" style={color ? ({ ["--accent" as any]: color }) : undefined}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {sub && <div className="sub">{sub}</div>}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="center" style={{ padding: 40, gap: 12, flexDirection: "column" as any }}>
      <div className="spinner" />
      <div className="faint" style={{ fontSize: 12 }}>{label}</div>
    </div>
  );
}

export function Chip({ children, kind = "" }: { children: ReactNode; kind?: string }) {
  return <span className={`chip ${kind}`}>{children}</span>;
}

const axisStyle = { fontSize: 11, fill: "var(--text-faint)" };
const tooltipStyle = {
  background: "var(--panel-2)", border: "1px solid var(--border-strong)",
  borderRadius: 0, color: "var(--text)", fontSize: 12,
};

export function BarViz({ data, height = 260, color = "#00d1ff", horizontal = false }:
  { data: { label: string; value: number }[]; height?: number; color?: string; horizontal?: boolean }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"}
        margin={{ top: 6, right: 12, bottom: 6, left: horizontal ? 20 : 0 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="var(--grid)" />
        {horizontal ? (
          <>
            <XAxis type="number" tick={axisStyle} stroke="var(--border)" />
            <YAxis type="category" dataKey="label" tick={axisStyle} width={110} stroke="var(--border)" />
          </>
        ) : (
          <>
            <XAxis dataKey="label" tick={axisStyle} stroke="var(--border)" angle={-20} textAnchor="end" height={54} interval={0} />
            <YAxis tick={axisStyle} stroke="var(--border)" />
          </>
        )}
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--grid)" }} />
        <Bar dataKey="value" fill={color} maxBarSize={38} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function LineViz({ data, height = 260, color = "#00d1ff", area = false }:
  { data: { label: string; value: number }[]; height?: number; color?: string; area?: boolean }) {
  const Chart: any = area ? AreaChart : LineChart;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data} margin={{ top: 6, right: 12, bottom: 6, left: 0 }}>
        <CartesianGrid strokeDasharray="2 4" stroke="var(--grid)" />
        <XAxis dataKey="label" tick={axisStyle} stroke="var(--border)" />
        <YAxis tick={axisStyle} stroke="var(--border)" />
        <Tooltip contentStyle={tooltipStyle} />
        {area
          ? <Area type="monotone" dataKey="value" stroke={color} fill={color} fillOpacity={0.15} strokeWidth={2} />
          : <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />}
      </Chart>
    </ResponsiveContainer>
  );
}

export function DonutViz({ data, height = 260 }:
  { data: { label: string; value: number }[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="label" innerRadius="55%" outerRadius="82%" paddingAngle={1}>
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="var(--panel)" />)}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function Legend({ data }: { data: { label: string; value: number }[] }) {
  const total = data.reduce((a, b) => a + b.value, 0) || 1;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
      {data.map((d, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
          <span style={{ width: 10, height: 10, background: COLORS[i % COLORS.length] }} />
          <span style={{ flex: 1 }}>{d.label}</span>
          <span className="dim">{d.value}</span>
          <span className="faint" style={{ width: 42, textAlign: "right" }}>
            {((d.value / total) * 100).toFixed(0)}%
          </span>
        </div>
      ))}
    </div>
  );
}
