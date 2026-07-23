import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useLang } from "../context";
import { Loading, Panel, Stat } from "../components";
import { NetworkGraph, GNode, GEdge } from "../NetworkGraph";

const BAND_COLOR: Record<string, string> = {
  Low: "#24d18b", Medium: "#ffb020", High: "#ff8a4d", Critical: "#ff4d5e",
};

export default function NetworkPage() {
  const { t } = useLang();
  const [gangs, setGangs] = useState<any[]>([]);
  const [gang, setGang] = useState("");
  const [minDeg, setMinDeg] = useState(2);
  const [graph, setGraph] = useState<any>(null);

  useEffect(() => { api.gangs().then(setGangs); }, []);
  useEffect(() => { setGraph(null); api.networkGraph(minDeg, gang).then(setGraph); }, [gang, minDeg]);

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [] as GNode[], edges: [] as GEdge[] };
    const nodes: GNode[] = graph.nodes.map((n: any) => ({
      id: n.id, label: n.label,
      color: BAND_COLOR[n.band] || "#00d1ff",
      size: 6 + Math.min(n.degree, 10),
      meta: `${n.district} · risk ${n.risk} (${n.band}) · ${n.degree} links`,
    }));
    const edges: GEdge[] = graph.edges.map((e: any) => ({
      source: e.source, target: e.target,
      color: e.gang ? "#a06bff" : "var(--border-strong)",
      width: e.strength > 2 ? 2 : 1,
    }));
    return { nodes, edges };
  }, [graph]);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid cols-4">
        <Stat label={t("Nodes (accused)")} value={nodes.length} />
        <Stat label={t("Associations")} value={edges.length} color="#a06bff" />
        <Stat label={t("Gangs tracked")} value={gangs.length} color="#ffb020" />
        <Stat label={t("Densest link")} value={gangs[0]?.name || "—"} sub={gangs[0] ? `${gangs[0].links} ${t("links")}` : ""} color="#ff4d5e" />
      </div>

      <Panel title={t("Criminal Network Graph")}
        right={
          <div style={{ display: "flex", gap: 8 }}>
            <select value={gang} onChange={(e) => setGang(e.target.value)}>
              <option value="">{t("All groups")}</option>
              {gangs.map((g) => <option key={g.name} value={g.name}>{g.name} ({g.links})</option>)}
            </select>
            <select value={minDeg} onChange={(e) => setMinDeg(Number(e.target.value))}>
              <option value={0}>{t("All nodes")}</option>
              <option value={2}>Degree ≥ 2</option>
              <option value={3}>Degree ≥ 3</option>
              <option value={4}>Degree ≥ 4</option>
            </select>
          </div>
        }>
        <div className="faint" style={{ fontSize: 12, marginBottom: 8 }}>
          Node colour = risk band · size = number of links · purple edges = gang/association links.
          Drag nodes to rearrange, hover to isolate connections.
        </div>
        {!graph ? <Loading label={t("Building network…")} /> :
          <NetworkGraph nodes={nodes} edges={edges} height={520} />}
      </Panel>

      <Panel title={t("Organised Groups / Repeat-offender Networks")}>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead><tr><th>{t("Group")}</th><th>{t("Association links")}</th></tr></thead>
            <tbody>
              {gangs.map((g) => (
                <tr key={g.name} style={{ cursor: "pointer" }} onClick={() => setGang(g.name)}>
                  <td>{g.name}</td><td>{g.links}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
