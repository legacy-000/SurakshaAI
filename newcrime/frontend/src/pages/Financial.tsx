import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useLang } from "../context";
import { BarViz, Chip, Loading, Panel, Stat } from "../components";
import { NetworkGraph, GNode, GEdge } from "../NetworkGraph";

export default function Financial() {
  const { t } = useLang();
  const [summary, setSummary] = useState<any>(null);
  const [graph, setGraph] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [onlyFlagged, setOnlyFlagged] = useState(true);

  useEffect(() => {
    api.financialSummary().then(setSummary);
    api.suspiciousAccounts().then(setAccounts);
  }, []);
  useEffect(() => { setGraph(null); api.moneyGraph(onlyFlagged).then(setGraph); }, [onlyFlagged]);

  const { nodes, edges } = useMemo(() => {
    if (!graph) return { nodes: [] as GNode[], edges: [] as GEdge[] };
    const nodes: GNode[] = graph.nodes.map((n: any) => ({
      id: n.id, label: n.label, color: n.suspicious ? "#ff4d5e" : "#2f81f7",
      size: n.suspicious ? 10 : 7, meta: `${n.bank} · ${n.type}${n.suspicious ? " · SUSPICIOUS" : ""}`,
    }));
    const edges: GEdge[] = graph.edges.map((e: any) => ({
      source: e.source, target: e.target,
      color: e.flagged ? "#ff4d5e" : "var(--border-strong)",
      width: e.flagged ? 2 : 1,
    }));
    return { nodes, edges };
  }, [graph]);

  if (!summary) return <Loading label={t("Loading financial intelligence…")} />;
  const inr = (n: number) => "₹" + Intl.NumberFormat("en-IN", { notation: "compact" }).format(n);

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="grid cols-4">
        <Stat label={t("Transactions")} value={summary.total_transactions} sub={`${summary.flagged} ${t("flagged")}`} />
        <Stat label={t("Suspicious Accounts")} value={summary.suspicious_accounts} color="#ff4d5e" />
        <Stat label={t("Flow Volume")} value={inr(summary.volume)} color="#2f81f7" />
        <Stat label={t("Reported Loss")} value={inr(summary.financial_loss)} color="#ffb020" />
      </div>

      <div className="grid cols-3">
        <Panel title={t("Transaction Channels")} className="" >
          <BarViz data={summary.by_channel} color="#a06bff" height={220} />
        </Panel>
        <Panel title={t("Money Trail Network")} className="" right={
          <label style={{ display: "flex", gap: 6, alignItems: "center", fontSize: 12 }}>
            <input type="checkbox" checked={onlyFlagged} onChange={(e) => setOnlyFlagged(e.target.checked)}
              style={{ width: 15, height: 15 }} /> {t("flagged only")}
          </label>
        } >
          <div style={{ gridColumn: "span 2" }} />
          {!graph ? <Loading /> : <NetworkGraph nodes={nodes} edges={edges} height={300} />}
        </Panel>
      </div>

      <Panel title={t("Suspicious Accounts — Inflow / Outflow")}>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead><tr><th>{t("Holder")}</th><th>{t("Bank")}</th><th>{t("Type")}</th><th>{t("Account")}</th>
              <th>{t("Inflow")}</th><th>{t("Outflow")}</th><th>{t("Txns")}</th></tr></thead>
            <tbody>
              {accounts.map((a) => (
                <tr key={a.id}>
                  <td>{a.holder}</td><td className="dim">{a.bank}</td>
                  <td><Chip>{a.type}</Chip></td>
                  <td className="mono" style={{ fontSize: 12 }}>{a.account_number}</td>
                  <td className="dim">{inr(a.inflow)}</td>
                  <td className="dim">{inr(a.outflow)}</td>
                  <td>{a.transactions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
