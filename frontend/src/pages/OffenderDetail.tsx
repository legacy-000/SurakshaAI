import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, FileDown } from "lucide-react";
import { api } from "../api";
import { useAuth, useLang } from "../context";
import { offenderDossier } from "../briefing";
import { Chip, Loading, Panel, Stat } from "../components";
import { NetworkGraph, GNode, GEdge } from "../NetworkGraph";

export default function OffenderDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user } = useAuth();
  const { t } = useLang();
  const [o, setO] = useState<any>(null);
  const [ego, setEgo] = useState<any>(null);

  useEffect(() => {
    api.offenderDetail(Number(id)).then(setO);
    api.egoNetwork(Number(id)).then(setEgo);
  }, [id]);

  const { nodes, edges } = useMemo(() => {
    if (!ego) return { nodes: [] as GNode[], edges: [] as GEdge[] };
    const nodes: GNode[] = [
      { id: ego.accused.id, label: ego.accused.name, color: "#00d1ff", size: 13, meta: "subject" },
      ...ego.associates.map((a: any) => ({
        id: a.id, label: a.name, color: "#a06bff", size: 8, meta: `${a.district} · ${a.status}`,
      })),
    ];
    const edges: GEdge[] = ego.links.map((l: any) => ({
      source: l.source, target: l.target, color: l.gang ? "#a06bff" : "var(--border-strong)",
    }));
    return { nodes, edges };
  }, [ego]);

  if (!o) return <Loading label={t("Loading offender profile…")} />;
  const p = o.profile;

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
        <button className="btn ghost" style={{ width: "fit-content" }} onClick={() => nav("/profiling")}>
          <ArrowLeft size={15} /> {t("Back to profiling")}
        </button>
        {user?.permissions.can_export &&
          <button className="btn" onClick={() => offenderDossier(o,
            { full_name: user.full_name, rank: user.rank, badge_number: user.badge_number })}>
            <FileDown size={15} /> {t("Generate dossier (PDF)")}
          </button>}
      </div>

      <div className="grid cols-4">
        <Stat label={t("Risk Score")} value={p.risk_score} sub={p.risk_band}
          color={p.risk_band === "Critical" || p.risk_band === "High" ? "#ff4d5e" : "#ffb020"} />
        <Stat label={t("Prior Convictions")} value={o.priors} />
        <Stat label={t("Linked Cases")} value={o.cases.length} color="#2f81f7" />
        <Stat label={t("Status")} value={o.status} color="#a06bff" />
      </div>

      <div className="grid cols-2">
        <Panel title={t("Offender Profile")}>
          <h2 style={{ margin: "0 0 6px" }}>{o.name} {p.habitual && <Chip kind="amber">habitual</Chip>}</h2>
          <div className="faint" style={{ marginBottom: 12 }}>{o.aliases && `alias: ${o.aliases} · `}{o.age}/{o.gender} · {o.district}</div>
          <Grid label={t("Occupation")} value={o.occupation} />
          <Grid label={t("Education")} value={o.education} />
          <Grid label={t("Socio-economic")} value={o.socio_economic} />
          <Grid label={t("Setting")} value={`${o.urban_rural}${o.migrant ? " · migrant" : ""}`} />
          <Grid label={t("Modus Operandi")} value={p.modus_operandi} />
          <div style={{ marginTop: 12 }}>
            <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>{t("BEHAVIOURAL TRAITS")}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {(p.traits || "").split(",").map((tg: string) => tg.trim()).filter(Boolean).map((tg: string) =>
                <span key={tg} className="chip">{tg}</span>)}
            </div>
          </div>
          <div style={{ marginTop: 12 }}>
            <div className="faint" style={{ fontSize: 12, marginBottom: 6 }}>{t("PROPENSITY")}</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {(p.propensity || "").split(",").map((tg: string) => tg.trim()).filter(Boolean).map((tg: string) =>
                <span key={tg} className="chip accent">{tg}</span>)}
            </div>
          </div>
        </Panel>

        <Panel title={t("Associate Network")}>
          {!ego ? <Loading /> : <NetworkGraph nodes={nodes} edges={edges} height={360}
            onNodeClick={(nid) => nid !== o.id && nav(`/offender/${nid}`)} />}
        </Panel>
      </div>

      <Panel title={t("Criminal History")}>
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead><tr><th>{t("FIR No.")}</th><th>{t("Title")}</th><th>{t("Crime Type")}</th><th>{t("Status")}</th><th>{t("Date")}</th></tr></thead>
            <tbody>
              {o.cases.map((c: any) => (
                <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => nav(`/cases/${c.id}`)}>
                  <td className="mono" style={{ fontSize: 12 }}>{c.fir_number}</td>
                  <td>{c.title}</td><td>{c.crime_type}</td>
                  <td><Chip>{c.status}</Chip></td>
                  <td className="dim">{c.date?.slice(0, 10)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function Grid({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", borderBottom: "1px solid var(--border)" }}>
      <span className="faint" style={{ fontSize: 13 }}>{label}</span>
      <span>{value}</span>
    </div>
  );
}
