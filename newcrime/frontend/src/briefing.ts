import jsPDF from "jspdf";

interface Officer { full_name: string; rank?: string; badge_number?: string; }

function header(doc: jsPDF, title: string, subtitle: string, officer?: Officer) {
  const W = doc.internal.pageSize.getWidth();
  doc.setFillColor(10, 14, 20);
  doc.rect(0, 0, W, 26, "F");
  doc.setTextColor(0, 209, 255);
  doc.setFontSize(9);
  doc.text("CRIME INTELLIGENCE PLATFORM · KARNATAKA", 14, 11);
  doc.setTextColor(230);
  doc.setFontSize(14);
  doc.text(title, 14, 20);
  doc.setTextColor(90);
  doc.setFontSize(8);
  doc.text(subtitle, 14, 32);
  doc.text(
    `Prepared by ${officer?.full_name || "—"}${officer?.rank ? ` (${officer.rank})` : ""} · ${new Date().toLocaleString()}`,
    14, 37
  );
  doc.setDrawColor(200);
  doc.line(14, 40, W - 14, 40);
  return 48;
}

function section(doc: jsPDF, y: number, label: string) {
  const W = doc.internal.pageSize.getWidth();
  if (y > 265) { doc.addPage(); y = 20; }
  doc.setFillColor(240, 243, 248);
  doc.rect(14, y - 5, W - 28, 8, "F");
  doc.setTextColor(30, 50, 90);
  doc.setFontSize(10);
  doc.setFont(undefined, "bold");
  doc.text(label.toUpperCase(), 16, y);
  doc.setFont(undefined, "normal");
  return y + 10;
}

function kv(doc: jsPDF, y: number, rows: [string, string][]) {
  doc.setFontSize(10);
  rows.forEach(([k, v]) => {
    if (y > 275) { doc.addPage(); y = 20; }
    doc.setTextColor(120);
    doc.text(`${k}:`, 16, y);
    doc.setTextColor(30);
    doc.text(doc.splitTextToSize(String(v ?? "—"), 130), 60, y);
    y += 6;
  });
  return y + 2;
}

function para(doc: jsPDF, y: number, text: string) {
  const W = doc.internal.pageSize.getWidth();
  doc.setFontSize(10); doc.setTextColor(40);
  const lines = doc.splitTextToSize(text || "—", W - 32);
  if (y + lines.length * 5 > 280) { doc.addPage(); y = 20; }
  doc.text(lines, 16, y);
  return y + lines.length * 5 + 4;
}

function footer(doc: jsPDF) {
  const W = doc.internal.pageSize.getWidth();
  const H = doc.internal.pageSize.getHeight();
  const n = doc.getNumberOfPages();
  for (let p = 1; p <= n; p++) {
    doc.setPage(p);
    doc.setFontSize(7); doc.setTextColor(150);
    doc.text("CONFIDENTIAL · For authorised law-enforcement use only · Evidence-backed, machine-generated draft — verify before action.",
      14, H - 8);
    doc.text(`Page ${p}/${n}`, W - 24, H - 8);
  }
}

export function caseBriefing(c: any, similar: any, extras?: any, officer?: Officer) {
  const bundle = extras?.bundle, notes = extras?.notes || [],
    witnesses = extras?.witnesses || [], evidence = extras?.evidence || [];
  const doc = new jsPDF();
  const ref = c.fir_number.replace(/[\/]/g, "-");
  let y = header(doc, `Case Briefing — ${c.fir_number}`, c.title, officer);

  // table of contents
  y = section(doc, y, "Contents");
  ["1. Case Summary", "2. Description", "3. Progress Status", "4. Suspect Summary",
   "5. Victim Summary", "6. Witness Summary", "7. Evidence Summary",
   "8. Investigation Notes", "9. Investigation Timeline", "10. Similar Cases",
   "11. Recommendations"].forEach((t) => { y = para(doc, y, t); });

  y = section(doc, y, "1. Case Summary");
  y = kv(doc, y, [
    ["FIR Number", c.fir_number], ["Crime Type", `${c.crime_type} (${c.crime_head})`],
    ["Severity", c.severity], ["Status", c.status],
    ["District", `${c.district} · ${c.station}`], ["Location", c.location_name],
    ["Occurred", c.occurrence_date?.slice(0, 10)], ["Modus Operandi", c.modus_operandi],
    ["Officer", c.investigation?.officer || "—"],
    ...(c.is_financial ? [["Reported Loss", `INR ${Number(c.loss_amount).toLocaleString("en-IN")}`] as [string, string]] : []),
  ]);
  y = section(doc, y, "2. Description");
  y = para(doc, y, c.description);

  y = section(doc, y, "3. Progress Status");
  y = kv(doc, y, [
    ["Current Stage", bundle?.current_stage || "—"],
    ["Progress", `${bundle?.progress ?? c.investigation?.progress ?? 0}%`],
    ["Stages Remaining", String(bundle?.remaining_stages ?? "—")],
  ]);

  y = section(doc, y, "4. Suspect Summary");
  y = para(doc, y, c.accused?.length ? c.accused.map((a: any) => `${a.name} (${a.role}, ${a.status})`).join("; ") : "None recorded.");
  y = section(doc, y, "5. Victim Summary");
  y = para(doc, y, c.victims?.length ? c.victims.map((v: any) => `${v.name} (${v.age}/${v.gender})`).join("; ") : "None recorded.");

  y = section(doc, y, "6. Witness Summary");
  if (witnesses.length) witnesses.forEach((w: any) =>
    y = para(doc, y, `• ${w.name} (${w.reliability} reliability): ${w.statement || "no statement"}`));
  else y = para(doc, y, "No witnesses recorded.");

  y = section(doc, y, "7. Evidence Summary");
  if (evidence.length) evidence.forEach((e: any) =>
    y = para(doc, y, `• [${e.category}] ${e.original_name} — ${e.ai_summary}`));
  else y = para(doc, y, "No evidence uploaded.");

  y = section(doc, y, "8. Investigation Notes");
  if (notes.length) notes.forEach((n: any) =>
    y = para(doc, y, `• ${new Date(n.created_at).toLocaleDateString()} — ${n.author}${n.pinned ? " [PINNED]" : ""}: ${n.content}`));
  else y = para(doc, y, "No notes recorded.");

  if (c.timeline?.length) {
    y = section(doc, y, "9. Investigation Timeline");
    c.timeline.forEach((e: any) => {
      y = para(doc, y, `• ${e.timestamp?.slice(0, 10)} — ${e.title} [${e.type}]: ${e.description}`);
    });
  }
  if (similar?.similar?.length) {
    y = section(doc, y, "10. Similar Past Cases (decision support)");
    similar.similar.forEach((s: any) => {
      y = para(doc, y, `• ${s.fir_number} — ${s.title} (${s.district}) · match ${s.match_score}% · outcome ${s.outcome}`);
    });
  }
  y = section(doc, y, "11. Recommendations");
  y = para(doc, y, "Machine-generated draft for investigator review. Verify all facts against "
    + "primary records before any operational or legal action.");
  footer(doc);
  doc.save(`case-briefing-${ref}.pdf`);
}

export function offenderDossier(o: any, officer?: Officer) {
  const doc = new jsPDF();
  const p = o.profile || {};
  let y = header(doc, `Offender Dossier — ${o.name}`, `Risk ${p.risk_score} (${p.risk_band})${p.habitual ? " · Habitual" : ""}`, officer);
  y = section(doc, y, "Profile");
  y = kv(doc, y, [
    ["Name", o.name], ["Aliases", o.aliases || "—"], ["Age / Gender", `${o.age} / ${o.gender}`],
    ["District", o.district], ["Status", o.status], ["Prior Convictions", o.priors],
    ["Occupation", o.occupation], ["Education", o.education],
    ["Socio-economic", o.socio_economic], ["Setting", `${o.urban_rural}${o.migrant ? " · migrant" : ""}`],
  ]);
  y = section(doc, y, "Risk Assessment");
  y = kv(doc, y, [["Risk Score", `${p.risk_score} / 100 (${p.risk_band})`],
    ["Habitual Offender", p.habitual ? "Yes" : "No"], ["Modus Operandi", p.modus_operandi],
    ["Propensity", p.propensity], ["Behavioural Traits", p.traits]]);
  y = section(doc, y, "Criminal History");
  if (o.cases?.length) o.cases.forEach((c: any) => {
    y = para(doc, y, `• ${c.fir_number} — ${c.title} (${c.crime_type}) · ${c.status} · ${c.date?.slice(0, 10)}`);
  });
  else y = para(doc, y, "No linked cases.");
  footer(doc);
  doc.save(`offender-dossier-${o.id}.pdf`);
}

export function commandBriefing(d: any, districts: any[], officer?: Officer) {
  const doc = new jsPDF();
  let y = header(doc, "Command Center Intelligence Brief", `${d.scope} scope · ${d.district}`, officer);
  y = section(doc, y, "Key Indicators");
  y = kv(doc, y, [
    ["Total Cases", d.kpis.total_cases], ["Open", d.kpis.open],
    ["Clearance Rate", `${d.kpis.clearance_rate}%`],
    ["FIRs this month", `${d.kpis.firs_this_month} (${d.kpis.firs_change >= 0 ? "+" : ""}${d.kpis.firs_change}% vs last)`],
    ["Arrests (30d)", d.kpis.arrests_month],
  ]);
  y = section(doc, y, "Priority Alerts");
  if (d.alerts?.length) d.alerts.forEach((a: any) => y = para(doc, y, `• [${a.severity}] ${a.title} — ${a.district} (${a.type})`));
  else y = para(doc, y, "No active alerts.");
  y = section(doc, y, "High-risk Offenders");
  d.offenders?.forEach((o: any) => y = para(doc, y, `• ${o.name} — risk ${o.risk} (${o.band}) · ${o.district}`));
  y = section(doc, y, "Predicted Hotspots");
  d.predictions?.forEach((p: any) => y = para(doc, y, `• ${p.crime} in ${p.area} — ${Math.round(p.prob * 100)}% (${p.level})`));
  y = section(doc, y, "District Incident Counts");
  [...districts].sort((a, b) => b.count - a.count).forEach((r: any) =>
    y = para(doc, y, `• ${r.district}: ${r.count} incidents · top: ${r.top_crime}`));
  footer(doc);
  doc.save(`command-brief-${Date.now()}.pdf`);
}
