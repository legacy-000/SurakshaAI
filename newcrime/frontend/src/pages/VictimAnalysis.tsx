import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, AlertTriangle, Shield, BarChart3, ArrowLeft, Brain, Share2, Clock, ChevronRight } from "lucide-react";
import { api } from "../api";
import { useLang } from "../context";
import { Chip, Loading, Panel, Stat } from "../components";
import { NetworkGraph, GNode, GEdge } from "../NetworkGraph";

const NODE_COLORS: Record<string, string> = {
  Victim: "#ff4d5e", Accused: "#ff8a4d", Case: "#00d1ff", Witness: "#24d18b",
  Officer: "#ffb020", Phone: "#a06bff", Address: "#888",
};

export default function VictimAnalysis() {
  const { t } = useLang();
  const nav = useNavigate();
  const [overview, setOverview] = useState<any>(null);
  const [crimeTypes, setCrimeTypes] = useState<any[]>([]);
  const [vulnerability, setVulnerability] = useState<any[]>([]);
  const [victims, setVictims] = useState<any[]>([]);
  const [tab, setTab] = useState<"overview" | "list" | "vulnerability">("overview");
  const [selectedVictim, setSelectedVictim] = useState<number | null>(null);

  useEffect(() => {
    api.victimOverview().then(setOverview);
    api.victimCrimeTypes().then(setCrimeTypes);
    api.victimVulnerability().then(setVulnerability);
    api.victimList({ limit: 50 }).then((d: any) => setVictims(d.victims || []));
  }, []);

  if (!overview) return <Loading label={t("Loading…")} />;

  if (selectedVictim !== null) {
    return <VictimDetail victimId={selectedVictim} onBack={() => setSelectedVictim(null)} t={t} />;
  }

  const tabs = [
    { key: "overview" as const, label: t("Overview") },
    { key: "list" as const, label: t("Victim List") },
    { key: "vulnerability" as const, label: t("Vulnerability Assessment") },
  ];

  return (
    <div className="grid" style={{ gap: 16, maxWidth: 1000, margin: "0 auto" }}>
      <div className="grid cols-4">
        <Panel>
          <div className="faint" style={{ fontSize: 11, textTransform: "uppercase" }}>{t("Total Victims")}</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "var(--accent)" }}>{overview.total}</div>
        </Panel>
        <Panel>
          <div className="faint" style={{ fontSize: 11, textTransform: "uppercase" }}>{t("Repeat Victims")}</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "var(--amber)" }}>{overview.repeat_victims}</div>
        </Panel>
        <Panel>
          <div className="faint" style={{ fontSize: 11, textTransform: "uppercase" }}>{t("Districts Affected")}</div>
          <div style={{ fontSize: 28, fontWeight: 700 }}>{overview.by_district.length}</div>
        </Panel>
        <Panel>
          <div className="faint" style={{ fontSize: 11, textTransform: "uppercase" }}>{t("High Vulnerability")}</div>
          <div style={{ fontSize: 28, fontWeight: 700, color: "var(--red, #e53e3e)" }}>
            {vulnerability.filter((v: any) => v.risk === "High").length}
          </div>
        </Panel>
      </div>

      <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--border)" }}>
        {tabs.map((tb) => (
          <button key={tb.key} onClick={() => setTab(tb.key)} className="nav-item"
            style={{ width: "auto", borderLeft: "none",
              borderBottom: tab === tb.key ? "2px solid var(--accent)" : "2px solid transparent",
              color: tab === tb.key ? "var(--accent)" : "var(--text-dim)" }}>
            {tb.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <>
          <div className="grid cols-2">
            <Panel title={t("Victims by Gender")}>
              {overview.by_gender.map((g: any) => (
                <div key={g.label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0",
                  borderBottom: "1px solid var(--border)" }}>
                  <span>{g.label}</span>
                  <b>{g.value}</b>
                </div>
              ))}
            </Panel>
            <Panel title={t("Victims by Age Group")}>
              {overview.by_age.map((a: any) => (
                <div key={a.label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0",
                  borderBottom: "1px solid var(--border)" }}>
                  <span>{a.label}</span>
                  <b>{a.value}</b>
                </div>
              ))}
            </Panel>
          </div>

          <Panel title={t("Victims by District")}>
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {overview.by_district.map((d: any) => (
                <div key={d.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 140, fontSize: 13 }}>{d.label}</span>
                  <div style={{ flex: 1, height: 18, background: "var(--bg)", border: "1px solid var(--border)", position: "relative" }}>
                    <div style={{ height: "100%", background: "var(--accent)", opacity: 0.7,
                      width: `${Math.min(100, (d.value / (overview.by_district[0]?.value || 1)) * 100)}%` }} />
                  </div>
                  <span style={{ width: 30, fontSize: 12, textAlign: "right" }}>{d.value}</span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title={t("Crime Types Affecting Victims")}>
            <div style={{ overflowX: "auto" }}>
              <table>
                <thead><tr><th>{t("Crime Type")}</th><th>{t("Victim Count")}</th></tr></thead>
                <tbody>
                  {crimeTypes.map((ct: any) => (
                    <tr key={ct.crime_type}>
                      <td><Chip kind="accent">{ct.crime_type}</Chip></td>
                      <td style={{ fontWeight: 600 }}>{ct.victim_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </>
      )}

      {tab === "list" && (
        <Panel title={t("All Victims")}>
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>{t("Name")}</th><th>{t("Age")}</th><th>{t("Gender")}</th>
                  <th>{t("District")}</th><th>{t("Occupation")}</th><th>{t("Cases")}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {victims.map((v: any) => (
                  <tr key={v.id} style={{ cursor: "pointer" }} onClick={() => setSelectedVictim(v.id)}>
                    <td style={{ fontWeight: 600 }}>{v.name}</td>
                    <td>{v.age || "—"}</td>
                    <td>{v.gender || "—"}</td>
                    <td className="dim">{v.district || "—"}</td>
                    <td className="dim">{v.occupation || "—"}</td>
                    <td>
                      <Chip kind={v.case_count > 1 ? "amber" : "accent"}>{v.case_count}</Chip>
                    </td>
                    <td><ChevronRight size={14} className="faint" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}

      {tab === "vulnerability" && (
        <Panel title={<span><AlertTriangle size={13} /> {t("Vulnerability Assessment")}</span> as any}>
          {vulnerability.length === 0 ? <div className="faint">{t("No data available.")}</div> : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {vulnerability.map((v: any) => (
                <div key={v.id} style={{ padding: "10px 12px", border: "1px solid var(--border)",
                  background: "var(--panel-2)", cursor: "pointer",
                  borderLeft: `3px solid ${v.risk === "High" ? "var(--red, #e53e3e)" : v.risk === "Medium" ? "var(--amber)" : "var(--green)"}` }}
                  onClick={() => setSelectedVictim(v.id)}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <b>{v.name}</b>
                    <Chip kind={v.risk === "High" ? "red" : v.risk === "Medium" ? "amber" : "accent"}>{v.risk} {t("Risk")}</Chip>
                  </div>
                  <div className="dim" style={{ fontSize: 12, marginTop: 4 }}>
                    {v.age && <span>{t("Age")}: {v.age} · </span>}
                    {v.gender && <span>{v.gender} · </span>}
                    {v.district && <span>{v.district} · </span>}
                    {v.case_count} {t("case(s)")}
                  </div>
                  {v.factors.length > 0 && (
                    <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
                      {v.factors.map((f: string, i: number) => (
                        <span key={i} style={{ padding: "2px 8px", fontSize: 11, border: "1px solid var(--border)",
                          background: "var(--bg)", color: "var(--text-dim)" }}>{f}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Panel>
      )}
    </div>
  );
}


function VictimDetail({ victimId, onBack, t }: { victimId: number; onBack: () => void; t: (s: string) => string }) {
  const [intel, setIntel] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [detailTab, setDetailTab] = useState<"intelligence" | "graph">("intelligence");
  const [nodeFilter, setNodeFilter] = useState("");
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    api.victimIntelligence(victimId).then(setIntel);
    api.victimRelationships(victimId).then(setGraph);
  }, [victimId]);

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [] as GNode[], edges: [] as GEdge[] };
    let filtered = graph.nodes;
    if (nodeFilter) {
      const ids = new Set(filtered.filter((n: any) => n.type === nodeFilter).map((n: any) => n.id));
      ids.add(`victim_${victimId}`);
      const edgeSet = new Set<string>();
      graph.edges.forEach((e: any) => {
        if (ids.has(e.source) || ids.has(e.target)) {
          edgeSet.add(e.source); edgeSet.add(e.target);
        }
      });
      filtered = graph.nodes.filter((n: any) => ids.has(n.id) || edgeSet.has(n.id));
    }
    const idSet = new Set(filtered.map((n: any) => n.id));
    const gNodes: GNode[] = filtered.map((n: any, i: number) => ({
      id: i,
      label: n.label,
      color: n.color || NODE_COLORS[n.type] || "#888",
      size: n.size || 8,
      meta: `${n.type} · ${n.meta || ""}`,
    }));
    const idxMap = new Map(filtered.map((n: any, i: number) => [n.id, i]));
    const gEdges: GEdge[] = graph.edges
      .filter((e: any) => idSet.has(e.source) && idSet.has(e.target))
      .map((e: any) => ({
        source: idxMap.get(e.source)!,
        target: idxMap.get(e.target)!,
        label: e.label,
        color: "var(--border-strong)",
        width: 1,
      }));
    return { nodes: gNodes, edges: gEdges };
  }, [graph, nodeFilter, victimId]);

  const nodeTypes = useMemo(() => {
    if (!graph) return [];
    const types = new Set<string>();
    graph.nodes.forEach((n: any) => types.add(n.type));
    return [...types].sort();
  }, [graph]);

  const selectedNodeData = useMemo(() => {
    if (!graph || selectedNode === null) return null;
    const idx = parseInt(selectedNode);
    if (isNaN(idx)) return null;
    const filteredNodes = nodeFilter
      ? graph.nodes.filter((n: any) => {
          const ids = new Set(graph.nodes.filter((nn: any) => nn.type === nodeFilter).map((nn: any) => nn.id));
          ids.add(`victim_${victimId}`);
          const edgeSet = new Set<string>();
          graph.edges.forEach((e: any) => {
            if (ids.has(e.source) || ids.has(e.target)) { edgeSet.add(e.source); edgeSet.add(e.target); }
          });
          return ids.has(n.id) || edgeSet.has(n.id);
        })
      : graph.nodes;
    return filteredNodes[idx] || null;
  }, [graph, selectedNode, nodeFilter, victimId]);

  if (!intel) return <Loading label={t("Loading…")} />;

  return (
    <div className="grid" style={{ gap: 16, maxWidth: 1100, margin: "0 auto" }}>
      <button className="btn ghost" onClick={onBack} style={{ justifySelf: "start" }}>
        <ArrowLeft size={15} /> {t("Back to Victim Analysis")}
      </button>

      <Panel>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 22 }}>{intel.name}</h2>
            <div className="faint" style={{ fontSize: 13, marginTop: 4 }}>
              {intel.case_count} {t("case(s)")} · {intel.year_range}
              {intel.is_repeat_victim && <Chip kind="amber" style={{ marginLeft: 8 }}>{t("Repeat Victim")}</Chip>}
            </div>
          </div>
        </div>
        <div style={{ marginTop: 12, padding: "10px 14px", background: "var(--bg)", border: "1px solid var(--border)",
          borderLeft: "3px solid var(--accent)", lineHeight: 1.6, fontSize: 14 }}>
          <Brain size={14} style={{ color: "var(--accent)", marginRight: 6, verticalAlign: "middle" }} />
          {intel.ai_summary}
        </div>
      </Panel>

      <div style={{ display: "flex", gap: 2, borderBottom: "1px solid var(--border)" }}>
        <button onClick={() => setDetailTab("intelligence")} className="nav-item"
          style={{ width: "auto", borderLeft: "none",
            borderBottom: detailTab === "intelligence" ? "2px solid var(--accent)" : "2px solid transparent",
            color: detailTab === "intelligence" ? "var(--accent)" : "var(--text-dim)" }}>
          <BarChart3 size={14} /> {t("Intelligence")}
        </button>
        <button onClick={() => setDetailTab("graph")} className="nav-item"
          style={{ width: "auto", borderLeft: "none",
            borderBottom: detailTab === "graph" ? "2px solid var(--accent)" : "2px solid transparent",
            color: detailTab === "graph" ? "var(--accent)" : "var(--text-dim)" }}>
          <Share2 size={14} /> {t("Relationship Graph")}
        </button>
      </div>

      {detailTab === "intelligence" && (
        <>
          <div className="grid cols-2">
            <Panel title={t("District Breakdown")}>
              {Object.entries(intel.district_breakdown).map(([d, cnt]: [string, any]) => (
                <div key={d} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0",
                  borderBottom: "1px solid var(--border)" }}>
                  <span>{d}</span>
                  <b>{cnt}</b>
                </div>
              ))}
              {Object.keys(intel.district_breakdown).length === 0 &&
                <div className="faint">{t("No data available.")}</div>}
            </Panel>
            <Panel title={t("Crime Type Breakdown")}>
              {Object.entries(intel.crime_breakdown).map(([ct, cnt]: [string, any]) => (
                <div key={ct} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0",
                  borderBottom: "1px solid var(--border)" }}>
                  <Chip kind="accent">{ct}</Chip>
                  <b>{cnt}</b>
                </div>
              ))}
              {Object.keys(intel.crime_breakdown).length === 0 &&
                <div className="faint">{t("No data available.")}</div>}
            </Panel>
          </div>

          <Panel title={<span><Clock size={14} /> {t("Case Timeline")}</span> as any}>
            {intel.timeline.length === 0 ? <div className="faint">{t("No cases recorded.")}</div> : (
              <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
                {intel.timeline.map((ev: any, i: number) => (
                  <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0",
                    borderBottom: i < intel.timeline.length - 1 ? "1px solid var(--border)" : "none" }}>
                    <div style={{ width: 90, flexShrink: 0, fontSize: 12, color: "var(--text-dim)" }}>
                      {ev.date ? new Date(ev.date).toLocaleDateString("en-IN", { year: "numeric", month: "short" }) : "—"}
                    </div>
                    <div style={{ width: 3, background: "var(--accent)", flexShrink: 0, borderRadius: 2 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{ev.fir_number || ev.title}</div>
                      <div className="dim" style={{ fontSize: 12 }}>
                        {ev.crime_type} · {ev.district} · <Chip kind={
                          ev.severity === "Critical" ? "red" : ev.severity === "High" ? "amber" : "accent"
                        }>{ev.status}</Chip>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel title={t("FIR History")}>
            {intel.fir_history.length === 0 ? <div className="faint">{t("No FIRs recorded.")}</div> : (
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {intel.fir_history.map((fir: string) => (
                  <Chip key={fir} kind="accent">{fir}</Chip>
                ))}
              </div>
            )}
          </Panel>
        </>
      )}

      {detailTab === "graph" && (
        <>
          <Panel title={t("Victim Relationship Graph")}
            right={
              <select value={nodeFilter} onChange={(e) => setNodeFilter(e.target.value)}
                style={{ padding: "4px 8px", fontSize: 12 }}>
                <option value="">{t("All node types")}</option>
                {nodeTypes.map(nt => <option key={nt} value={nt}>{nt}</option>)}
              </select>
            }>
            <div style={{ display: "flex", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
              {Object.entries(NODE_COLORS).map(([type, color]) => (
                <span key={type} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11 }}>
                  <span style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block" }} />
                  {type}
                </span>
              ))}
            </div>
            {!graph ? <Loading label={t("Building graph…")} /> :
              nodes.length === 0 ? <div className="faint center" style={{ height: 200 }}>{t("No relationship data available.")}</div> :
              <NetworkGraph nodes={nodes} edges={edges} height={480}
                onNodeClick={(id) => setSelectedNode(String(id))} />}
          </Panel>

          {selectedNodeData && (
            <Panel title={t("Node Detail")}>
              <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <span style={{ width: 16, height: 16, borderRadius: "50%",
                  background: NODE_COLORS[selectedNodeData.type] || "#888", display: "inline-block" }} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{selectedNodeData.label}</div>
                  <div className="faint" style={{ fontSize: 12 }}>{selectedNodeData.type} · {selectedNodeData.meta}</div>
                </div>
              </div>
            </Panel>
          )}
        </>
      )}
    </div>
  );
}
