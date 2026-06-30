import React from "react";

interface KPICardProps {
  title: string;
  value: string;
  change: string;
}

export default function KPICard({ title, value, change }: KPICardProps) {
  return (
    <div className="bg-card p-6 rounded-xl border flex flex-col space-y-2">
      <span className="text-sm font-medium text-muted-foreground">{title}</span>
      <span className="text-3xl font-bold tracking-tight">{value}</span>
      <span className="text-xs text-primary font-medium">{change}</span>
    </div>
  );
}
