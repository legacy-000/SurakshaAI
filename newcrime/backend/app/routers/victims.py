"""Victim Analysis module: demographics, trends, vulnerability, intelligence, relationship graph."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, case as sql_case
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/victims", tags=["victims"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    total = db.query(func.count(m.Victim.id)).scalar() or 0
    by_gender = (db.query(m.Victim.gender, func.count(m.Victim.id))
                 .group_by(m.Victim.gender).all())
    band = sql_case(
        (m.Victim.age < 18, "Under 18"),
        (m.Victim.age < 25, "18-24"),
        (m.Victim.age < 35, "25-34"),
        (m.Victim.age < 45, "35-44"),
        (m.Victim.age < 60, "45-59"),
        else_="60+",
    )
    by_age = db.query(band, func.count(m.Victim.id)).group_by(band).all()
    by_district = (db.query(m.Victim.district, func.count(m.Victim.id))
                   .group_by(m.Victim.district)
                   .order_by(func.count(m.Victim.id).desc()).limit(10).all())
    repeat = (db.query(m.Victim.id, func.count(m.CaseVictim.case_id))
              .join(m.CaseVictim, m.Victim.id == m.CaseVictim.victim_id)
              .group_by(m.Victim.id)
              .having(func.count(m.CaseVictim.case_id) > 1).count())
    return {
        "total": total,
        "repeat_victims": repeat,
        "by_gender": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_gender],
        "by_age": [{"label": r[0], "value": r[1]} for r in by_age],
        "by_district": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_district],
    }


@router.get("/crime-types")
def crime_types(db: Session = Depends(get_db)):
    rows = (db.query(m.Case.crime_type, func.count(m.CaseVictim.id))
            .join(m.CaseVictim, m.Case.id == m.CaseVictim.case_id)
            .group_by(m.Case.crime_type)
            .order_by(func.count(m.CaseVictim.id).desc()).all())
    return [{"crime_type": r[0], "victim_count": r[1]} for r in rows]


@router.get("/list")
def list_victims(db: Session = Depends(get_db), district: str = "",
                 gender: str = "", limit: int = 50, offset: int = 0):
    q = db.query(m.Victim)
    if district:
        q = q.filter(m.Victim.district == district)
    if gender:
        q = q.filter(m.Victim.gender == gender)
    total = q.count()
    rows = q.order_by(m.Victim.created_at.desc()).offset(offset).limit(limit).all()
    result = []
    for v in rows:
        case_count = (db.query(func.count(m.CaseVictim.id))
                      .filter(m.CaseVictim.victim_id == v.id).scalar() or 0)
        result.append({
            "id": v.id, "name": v.full_name, "gender": v.gender, "age": v.age,
            "district": v.district, "occupation": v.occupation,
            "case_count": case_count,
        })
    return {"total": total, "victims": result}


@router.get("/vulnerability/assessment")
def vulnerability(db: Session = Depends(get_db)):
    rows = (db.query(m.Victim.id, m.Victim.full_name, m.Victim.age,
                     m.Victim.gender, m.Victim.district,
                     func.count(m.CaseVictim.case_id).label("case_count"))
            .join(m.CaseVictim, m.Victim.id == m.CaseVictim.victim_id)
            .group_by(m.Victim.id)
            .order_by(func.count(m.CaseVictim.case_id).desc())
            .limit(20).all())
    result = []
    for r in rows:
        risk = "High" if r.case_count > 2 else ("Medium" if r.case_count > 1 else "Low")
        factors = []
        if r.age and r.age < 18:
            factors.append("Minor")
        if r.age and r.age > 60:
            factors.append("Senior citizen")
        if r.case_count > 1:
            factors.append(f"Repeat victim ({r.case_count} cases)")
        result.append({
            "id": r.id, "name": r.full_name, "age": r.age, "gender": r.gender,
            "district": r.district, "case_count": r.case_count,
            "risk": risk, "factors": factors,
        })
    return result


@router.get("/{victim_id}/intelligence")
def victim_intelligence(victim_id: int, db: Session = Depends(get_db)):
    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")

    cases = (db.query(m.Case).join(m.CaseVictim, m.Case.id == m.CaseVictim.case_id)
             .filter(m.CaseVictim.victim_id == victim_id)
             .order_by(m.Case.occurrence_date.asc()).all())
    case_count = len(cases)

    by_district: dict[str, int] = {}
    by_crime: dict[str, int] = {}
    firs: list[str] = []
    timeline: list[dict] = []
    years: list[int] = []

    for c in cases:
        d = c.district or "Unknown"
        by_district[d] = by_district.get(d, 0) + 1
        ct = c.crime_type or "Unknown"
        by_crime[ct] = by_crime.get(ct, 0) + 1
        if c.fir_number:
            firs.append(c.fir_number)
        yr = c.occurrence_date.year if c.occurrence_date else None
        if yr:
            years.append(yr)
        timeline.append({
            "case_id": c.id, "fir_number": c.fir_number, "title": c.title,
            "crime_type": ct, "district": d, "status": c.status,
            "severity": c.severity,
            "date": c.occurrence_date.isoformat() if c.occurrence_date else None,
        })

    is_repeat = case_count > 1
    year_range = f"{min(years)}-{max(years)}" if years else "N/A"

    if case_count == 0:
        summary = f"{v.full_name} has no recorded cases in the system."
    elif case_count == 1:
        c0 = cases[0]
        summary = (f"{v.full_name} appeared as a victim in 1 {c0.crime_type or 'crime'} case"
                   f" in {c0.district or 'an unknown district'}"
                   f" ({c0.occurrence_date.strftime('%B %Y') if c0.occurrence_date else 'date unknown'}).")
    else:
        top_crime = max(by_crime, key=by_crime.get)
        top_district = max(by_district, key=by_district.get)
        def _pl(n: int) -> str:
            return "case" if n == 1 else "cases"
        summary = (f"{v.full_name} appeared in {case_count} cases across "
                   f"{len(by_district)} district(s) between {year_range}. "
                   f"Most frequent crime type: {top_crime} ({by_crime[top_crime]} {_pl(by_crime[top_crime])}). "
                   f"Most affected district: {top_district} ({by_district[top_district]} {_pl(by_district[top_district])}).")
        if is_repeat:
            summary += " Flagged as a repeat victim."

    return {
        "victim_id": victim_id,
        "name": v.full_name,
        "case_count": case_count,
        "is_repeat_victim": is_repeat,
        "fir_history": firs,
        "district_breakdown": by_district,
        "crime_breakdown": by_crime,
        "year_range": year_range,
        "timeline": timeline,
        "ai_summary": summary,
    }


@router.get("/{victim_id}/relationships")
def victim_relationships(victim_id: int, db: Session = Depends(get_db)):
    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")

    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()

    def add_node(nid: str, label: str, ntype: str, color: str, size: int = 8, meta: str = ""):
        if nid not in seen_nodes:
            seen_nodes.add(nid)
            nodes.append({"id": nid, "label": label, "type": ntype, "color": color, "size": size, "meta": meta})

    def add_edge(src: str, tgt: str, label: str):
        edges.append({"source": src, "target": tgt, "label": label})

    victim_nid = f"victim_{victim_id}"
    add_node(victim_nid, v.full_name, "Victim", "#ff4d5e", 14, f"Victim · {v.district or 'Unknown'}")

    case_ids = [cv.case_id for cv in db.query(m.CaseVictim).filter(m.CaseVictim.victim_id == victim_id).all()]
    cases = db.query(m.Case).filter(m.Case.id.in_(case_ids)).all() if case_ids else []

    for c in cases:
        cnid = f"case_{c.id}"
        add_node(cnid, c.fir_number or c.title, "Case", "#00d1ff", 10,
                 f"{c.crime_type} · {c.status} · {c.district}")
        add_edge(victim_nid, cnid, "Victim In")

        acc_links = db.query(m.CaseAccused).filter(m.CaseAccused.case_id == c.id).all()
        for al in acc_links:
            acc = db.get(m.Accused, al.accused_id)
            if not acc:
                continue
            anid = f"accused_{acc.id}"
            add_node(anid, acc.full_name, "Accused", "#ff8a4d", 10,
                     f"{acc.status} · {acc.district or 'Unknown'}")
            add_edge(anid, cnid, al.role_in_crime or "Accused In")

            if acc.phone_number:
                pnid = f"phone_{acc.phone_number}"
                add_node(pnid, acc.phone_number, "Phone", "#a06bff", 6, "Phone number")
                add_edge(anid, pnid, "Uses Phone")

            if acc.address:
                short_addr = acc.address[:30]
                addr_key = acc.address.strip().lower()[:40]
                addr_nid = f"addr_{hash(addr_key) % 100000}"
                add_node(addr_nid, short_addr, "Address", "#888", 6, acc.address)
                add_edge(anid, addr_nid, "Lives At")

        other_victims = db.query(m.CaseVictim).filter(
            m.CaseVictim.case_id == c.id, m.CaseVictim.victim_id != victim_id).all()
        for ov in other_victims:
            ov_rec = db.get(m.Victim, ov.victim_id)
            if not ov_rec:
                continue
            ovnid = f"victim_{ov.victim_id}"
            add_node(ovnid, ov_rec.full_name, "Victim", "#ff4d5e", 8,
                     f"Victim · {ov_rec.district or 'Unknown'}")
            add_edge(ovnid, cnid, "Victim In")

        witnesses = db.query(m.Witness).filter(m.Witness.case_id == c.id).all()
        for w in witnesses:
            wnid = f"witness_{w.id}"
            add_node(wnid, w.name, "Witness", "#24d18b", 7, f"Reliability: {w.reliability}")
            add_edge(wnid, cnid, "Witness In")

        inv = db.query(m.Investigation).filter(m.Investigation.case_id == c.id).first()
        if inv and inv.officer_id:
            off = db.get(m.Officer, inv.officer_id)
            if off:
                onid = f"officer_{off.id}"
                add_node(onid, off.name, "Officer", "#ffb020", 8,
                         f"{off.rank} · {off.posting_station}")
                add_edge(onid, cnid, "Investigating")

    if v.contact_number:
        vpnid = f"phone_{v.contact_number}"
        add_node(vpnid, v.contact_number, "Phone", "#a06bff", 6, "Victim phone")
        add_edge(victim_nid, vpnid, "Uses Phone")
        for n in nodes:
            if n["type"] == "Phone" and n["id"] != vpnid and n["label"] == v.contact_number:
                add_edge(vpnid, n["id"], "Same Phone")

    if v.address:
        short_addr = v.address[:30]
        addr_key = v.address.strip().lower()[:40]
        vaddr_nid = f"addr_{hash(addr_key) % 100000}"
        already_exists = vaddr_nid in seen_nodes
        add_node(vaddr_nid, short_addr, "Address", "#888", 6, v.address)
        add_edge(victim_nid, vaddr_nid, "Lives At")
        if already_exists:
            for e in edges:
                if e["source"] != victim_nid and e["target"] == vaddr_nid and e["label"] == "Lives At":
                    add_edge(victim_nid, e["source"], "Lives Together")
                    break

    return {"nodes": nodes, "edges": edges}


@router.get("/{victim_id}")
def victim_detail(victim_id: int, db: Session = Depends(get_db)):
    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")
    cases = (db.query(m.Case).join(m.CaseVictim, m.Case.id == m.CaseVictim.case_id)
             .filter(m.CaseVictim.victim_id == victim_id).all())
    return {
        "id": v.id, "name": v.full_name, "gender": v.gender, "age": v.age,
        "contact": v.contact_number, "address": v.address,
        "district": v.district, "occupation": v.occupation,
        "statement_summary": v.statement_summary,
        "cases": [{"id": c.id, "fir_number": c.fir_number, "title": c.title,
                   "crime_type": c.crime_type, "status": c.status, "severity": c.severity,
                   "district": c.district, "date": c.occurrence_date.isoformat() if c.occurrence_date else None}
                  for c in cases],
    }
