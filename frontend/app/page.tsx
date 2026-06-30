"use client";

import React from "react";
// Import placeholder modules to verify project structure linkages
import Navbar from "../components/navbar/navbar";
import Sidebar from "../components/sidebar/sidebar";
import KPICard from "../components/cards/kpi-card";
import CrimeTrendChart from "../components/charts/crime-trend-chart";
import LeafletMap from "../components/maps/leaflet-map";
import NetworkGraph from "../components/graph/network-graph";
import CaseTimeline from "../components/timeline/case-timeline";

export default function DashboardPage() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar Navigation */}
      <Sidebar />

      <div className="flex flex-1 flex-col overflow-y-auto">
        {/* Header Bar */}
        <Navbar />

        {/* Dashboard Main Workspace */}
        <main className="p-6 space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold tracking-tight">Precinct Intelligence Dashboard</h1>
            <span className="text-sm text-muted-foreground">Karnataka Police Command Center</span>
          </div>

          {/* Grid of KPI Metrics */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <KPICard title="Total Active FIRs" value="124" change="+4% from last week" />
            <KPICard title="Hotspot Alerts" value="8" change="2 critical severity" />
            <KPICard title="Assigned Officers" value="42" change="10 on active duty" />
            <KPICard title="AI Prediction Accuracy" value="94.2%" change="Optimized via RAG" />
          </div>

          {/* Visualizing Maps and Analytics Grid */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* GIS mapping layer */}
            <div className="lg:col-span-2 bg-card p-4 rounded-xl border">
              <h2 className="text-lg font-semibold mb-3">Live Crime Hotspot Mapping</h2>
              <div className="h-[400px]">
                <LeafletMap />
              </div>
            </div>

            {/* Recharts Analytics Panel */}
            <div className="bg-card p-4 rounded-xl border">
              <h2 className="text-lg font-semibold mb-3">Modus Operandi Trends</h2>
              <div className="h-[400px]">
                <CrimeTrendChart />
              </div>
            </div>
          </div>

          {/* Suspect graphs and Timeline Event logs */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="bg-card p-4 rounded-xl border">
              <h2 className="text-lg font-semibold mb-3">Suspect-Case Link Analysis Graph</h2>
              <div className="h-[350px]">
                <NetworkGraph />
              </div>
            </div>

            <div className="bg-card p-4 rounded-xl border">
              <h2 className="text-lg font-semibold mb-3">Case Progression chronological logs</h2>
              <div className="h-[350px] overflow-y-auto">
                <CaseTimeline />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
