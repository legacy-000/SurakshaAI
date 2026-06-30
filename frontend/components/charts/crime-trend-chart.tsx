import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const data = [
  { month: "Jan", incidents: 42 },
  { month: "Feb", incidents: 55 },
  { month: "Mar", incidents: 48 },
  { month: "Apr", incidents: 70 },
  { month: "May", incidents: 64 },
  { month: "Jun", incidents: 85 },
];

export default function CrimeTrendChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="month" stroke="#829ab1" />
        <YAxis stroke="#829ab1" />
        <Tooltip cursor={{ fill: "rgba(0, 0, 0, 0.05)" }} />
        <Bar dataKey="incidents" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
