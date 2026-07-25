"""Victim Analysis module: demographics, trends, vulnerability, intelligence, relationship graph."""
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, case as sql_case
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from .. import models as m
from ..deps import get_ctx

router = APIRouter(prefix="/api/victims", tags=["victims"])


@router.get("/overview")
def overview(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        victims = get_ctx(request).scope_rows(store.query("SELECT * FROM victims"))
        links = store.query("SELECT * FROM case_victim")
        total = len(victims)
        by_gender = Counter(v.get("gender") or "Unknown" for v in victims)
        order = ["Under 18", "18-24", "25-34", "35-44", "45-59", "60+"]
        by_age: dict[str, int] = {b: 0 for b in order}
        for v in victims:
            age = int(v.get("age") or 0)
            if age < 18: by_age["Under 18"] += 1
            elif age < 25: by_age["18-24"] += 1
            elif age < 35: by_age["25-34"] += 1
            elif age < 45: by_age["35-44"] += 1
            elif age < 60: by_age["45-59"] += 1
            else: by_age["60+"] += 1
        by_district = Counter(v.get("district") or "Unknown" for v in victims).most_common(10)
        victim_case_counts = Counter(l.get("victim_id") for l in links)
        repeat = sum(1 for c in victim_case_counts.values() if c > 1)
        return {
            "total": total, "repeat_victims": repeat,
            "by_gender": [{"label": k, "value": v} for k, v in by_gender.items()],
            "by_age": [{"label": k, "value": by_age[k]} for k in order],
            "by_district": [{"label": k, "value": v} for k, v in by_district],
        }

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
        "total": total, "repeat_victims": repeat,
        "by_gender": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_gender],
        "by_age": [{"label": r[0], "value": r[1]} for r in by_age],
        "by_district": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_district],
    }


@router.get("/crime-types")
def crime_types(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        links = store.query("SELECT * FROM case_victim")
        cases = {c.get("ROWID"): c for c in store.query("SELECT * FROM cases")}
        counts: dict[str, int] = {}
        for l in links:
            ct = cases.get(l.get("case_id"), {}).get("crime_type", "Unknown")
            counts[ct] = counts.get(ct, 0) + 1
        return sorted([{"crime_type": k, "victim_count": v} for k, v in counts.items()],
                      key=lambda x: -x["victim_count"])

    rows = (db.query(m.Case.crime_type, func.count(m.CaseVictim.id))
            .join(m.CaseVictim, m.Case.id == m.CaseVictim.case_id)
            .group_by(m.Case.crime_type)
            .order_by(func.count(m.CaseVictim.id).desc()).all())
    return [{"crime_type": r[0], "victim_count": r[1]} for r in rows]


@router.get("/list")
def list_victims(request: Request, db: Session = Depends(get_db), district: str = "",
                 gender: str = "", limit: int = 50, offset: int = 0):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        victims = get_ctx(request).scope_rows(store.query("SELECT * FROM victims"))
        if district:
            victims = [v for v in victims if v.get("district") == district]
        if gender:
            victims = [v for v in victims if v.get("gender") == gender]
        total = len(victims)
        page = victims[offset:offset + limit]
        links = store.query("SELECT * FROM case_victim")
        link_counts = Counter(l.get("victim_id") for l in links)
        return {"total": total, "victims": [
            {"id": v.get("ROWID"), "name": v.get("full_name"), "gender": v.get("gender"),
             "age": v.get("age"), "district": v.get("district"),
             "occupation": v.get("occupation"),
             "case_count": link_counts.get(v.get("ROWID"), 0)}
            for v in page]}

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
def vulnerability(request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        victims = get_ctx(request).scope_rows(store.query("SELECT * FROM victims"))
        links = store.query("SELECT * FROM case_victim")
        v_case_counts = Counter(l.get("victim_id") for l in links)
        scored = [(v, v_case_counts.get(v.get("ROWID"), 0)) for v in victims]
        scored.sort(key=lambda x: -x[1])
        result = []
        for v, cc in scored[:20]:
            risk = "High" if cc > 2 else ("Medium" if cc > 1 else "Low")
            factors = []
            age = int(v.get("age") or 0)
            if age and age < 18: factors.append("Minor")
            if age and age > 60: factors.append("Senior citizen")
            if cc > 1: factors.append(f"Repeat victim ({cc} cases)")
            result.append({"id": v.get("ROWID"), "name": v.get("full_name"),
                           "age": v.get("age"), "gender": v.get("gender"),
                           "district": v.get("district"), "case_count": cc,
                           "risk": risk, "factors": factors})
        return result

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
        if r.age and r.age < 18: factors.append("Minor")
        if r.age and r.age > 60: factors.append("Senior citizen")
        if r.case_count > 1: factors.append(f"Repeat victim ({r.case_count} cases)")
        result.append({"id": r.id, "name": r.full_name, "age": r.age, "gender": r.gender,
                       "district": r.district, "case_count": r.case_count,
                       "risk": risk, "factors": factors})
    return result


@router.get("/{victim_id}/intelligence")
def victim_intelligence(victim_id: int, request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        v = store.get("victims", victim_id)
        if v and not get_ctx(request).can_access_district(v.get("district")):
            v = None  # outside territory — indistinguishable from missing
        if not v:
            raise HTTPException(404, "victim not found")
        links = store.query(f"SELECT * FROM case_victim WHERE victim_id = {victim_id}")
        case_ids = [l.get("case_id") for l in links]
        cases = [store.get("cases", cid) for cid in case_ids]
        cases = [c for c in cases if c]
        return _build_intelligence(v, cases, victim_id)

    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")
    cases = (db.query(m.Case).join(m.CaseVictim, m.Case.id == m.CaseVictim.case_id)
             .filter(m.CaseVictim.victim_id == victim_id)
             .order_by(m.Case.occurrence_date.asc()).all())
    return _build_intelligence_orm(v, cases, victim_id)


@router.get("/{victim_id}/relationships")
def victim_relationships(victim_id: int, request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        v = store.get("victims", victim_id)
        if v and not get_ctx(request).can_access_district(v.get("district")):
            v = None  # outside territory — indistinguishable from missing
        if not v:
            raise HTTPException(404, "victim not found")
        return _build_relationships_catalyst(store, v, victim_id)

    v = db.get(m.Victim, victim_id)
    if not v:
        raise HTTPException(404, "victim not found")
    return _build_relationships_orm(db, v, victim_id)


@router.get("/{victim_id}")
def victim_detail(victim_id: int, request: Request, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        v = store.get("victims", victim_id)
        if v and not get_ctx(request).can_access_district(v.get("district")):
            v = None  # outside territory — indistinguishable from missing
        if not v:
            raise HTTPException(404, "victim not found")
        links = store.query(f"SELECT * FROM case_victim WHERE victim_id = {victim_id}")
        case_ids = [l.get("case_id") for l in links]
        cases = [store.get("cases", cid) for cid in case_ids]
        cases = [c for c in cases if c]
        return {
            "id": victim_id, "name": v.get("full_name"), "gender": v.get("gender"),
            "age": v.get("age"), "contact": v.get("contact_number"),
            "address": v.get("address"), "district": v.get("district"),
            "occupation": v.get("occupation"),
            "statement_summary": v.get("statement_summary"),
            "cases": [{"id": c.get("ROWID"), "fir_number": c.get("fir_number"),
                       "title": c.get("title"), "crime_type": c.get("crime_type"),
                       "status": c.get("status"), "severity": c.get("severity"),
                       "district": c.get("district"), "date": c.get("occurrence_date")}
                      for c in cases],
        }

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


def _build_intelligence(v: dict, cases: list[dict], victim_id: int):
    case_count = len(cases)
    by_district: dict[str, int] = {}
    by_crime: dict[str, int] = {}
    firs: list[str] = []
    timeline: list[dict] = []
    years: list[int] = []
    name = v.get("full_name", "")

    for c in cases:
        d = c.get("district") or "Unknown"
        by_district[d] = by_district.get(d, 0) + 1
        ct = c.get("crime_type") or "Unknown"
        by_crime[ct] = by_crime.get(ct, 0) + 1
        fir = c.get("fir_number")
        if fir:
            firs.append(fir)
        occ = c.get("occurrence_date")
        try:
            yr = int(str(occ)[:4]) if occ else None
        except (ValueError, TypeError):
            yr = None
        if yr:
            years.append(yr)
        timeline.append({
            "case_id": c.get("ROWID"), "fir_number": fir, "title": c.get("title"),
            "crime_type": ct, "district": d, "status": c.get("status"),
            "severity": c.get("severity"), "date": occ,
        })

    is_repeat = case_count > 1
    year_range = f"{min(years)}-{max(years)}" if years else "N/A"
    summary = _build_summary(name, cases, case_count, by_crime, by_district, year_range, is_repeat)

    return {
        "victim_id": victim_id, "name": name, "case_count": case_count,
        "is_repeat_victim": is_repeat, "fir_history": firs,
        "district_breakdown": by_district, "crime_breakdown": by_crime,
        "year_range": year_range, "timeline": timeline, "ai_summary": summary,
    }


def _build_intelligence_orm(v, cases, victim_id):
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

    cases_as_dicts = [{"crime_type": c.crime_type, "district": c.district,
                       "occurrence_date": c.occurrence_date.strftime('%B %Y') if c.occurrence_date else "date unknown"}
                      for c in cases]
    summary = _build_summary(v.full_name, cases_as_dicts, case_count, by_crime, by_district,
                             year_range, is_repeat)

    return {
        "victim_id": victim_id, "name": v.full_name, "case_count": case_count,
        "is_repeat_victim": is_repeat, "fir_history": firs,
        "district_breakdown": by_district, "crime_breakdown": by_crime,
        "year_range": year_range, "timeline": timeline, "ai_summary": summary,
    }


def _build_summary(name, cases, case_count, by_crime, by_district, year_range, is_repeat):
    if case_count == 0:
        return f"{name} has no recorded cases in the system."
    if case_count == 1:
        c0 = cases[0]
        ct = c0.get("crime_type") or c0.get("crime_type", "crime")
        dist = c0.get("district") or "an unknown district"
        return f"{name} appeared as a victim in 1 {ct} case in {dist}."
    top_crime = max(by_crime, key=by_crime.get)
    top_district = max(by_district, key=by_district.get)
    def _pl(n): return "case" if n == 1 else "cases"
    summary = (f"{name} appeared in {case_count} cases across "
               f"{len(by_district)} district(s) between {year_range}. "
               f"Most frequent crime type: {top_crime} ({by_crime[top_crime]} {_pl(by_crime[top_crime])}). "
               f"Most affected district: {top_district} ({by_district[top_district]} {_pl(by_district[top_district])}).")
    if is_repeat:
        summary += " Flagged as a repeat victim."
    return summary


def _build_relationships_catalyst(store, v, victim_id):
    nodes, edges, seen = [], [], set()

    def add_node(nid, label, ntype, color, size=8, meta=""):
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "label": label, "type": ntype, "color": color,
                          "size": size, "meta": meta})

    def add_edge(src, tgt, label):
        edges.append({"source": src, "target": tgt, "label": label})

    victim_nid = f"victim_{victim_id}"
    add_node(victim_nid, v.get("full_name"), "Victim", "#ff4d5e", 14,
             f"Victim · {v.get('district', 'Unknown')}")

    links = store.query(f"SELECT * FROM case_victim WHERE victim_id = {victim_id}")
    case_ids = [l.get("case_id") for l in links]
    for cid in case_ids:
        c = store.get("cases", cid)
        if not c:
            continue
        cnid = f"case_{cid}"
        add_node(cnid, c.get("fir_number") or c.get("title"), "Case", "#00d1ff", 10,
                 f"{c.get('crime_type')} · {c.get('status')} · {c.get('district')}")
        add_edge(victim_nid, cnid, "Victim In")

        acc_links = store.query(f"SELECT * FROM case_accused WHERE case_id = {cid}")
        for al in acc_links:
            acc = store.get("accused", al.get("accused_id"))
            if not acc:
                continue
            anid = f"accused_{al.get('accused_id')}"
            add_node(anid, acc.get("full_name"), "Accused", "#ff8a4d", 10,
                     f"{acc.get('status')} · {acc.get('district', 'Unknown')}")
            add_edge(anid, cnid, al.get("role_in_crime") or "Accused In")

        ov_links = store.query(f"SELECT * FROM case_victim WHERE case_id = {cid}")
        for ov in ov_links:
            if ov.get("victim_id") == victim_id:
                continue
            ov_rec = store.get("victims", ov.get("victim_id"))
            if not ov_rec:
                continue
            ovnid = f"victim_{ov.get('victim_id')}"
            add_node(ovnid, ov_rec.get("full_name"), "Victim", "#ff4d5e", 8,
                     f"Victim · {ov_rec.get('district', 'Unknown')}")
            add_edge(ovnid, cnid, "Victim In")

        witnesses = store.query(f"SELECT * FROM witnesses WHERE case_id = {cid}")
        for w in witnesses:
            wnid = f"witness_{w.get('ROWID')}"
            add_node(wnid, w.get("name"), "Witness", "#24d18b", 7,
                     f"Reliability: {w.get('reliability')}")
            add_edge(wnid, cnid, "Witness In")

    return {"nodes": nodes, "edges": edges}


def _build_relationships_orm(db, v, victim_id):
    nodes, edges, seen = [], [], set()

    def add_node(nid, label, ntype, color, size=8, meta=""):
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, "label": label, "type": ntype, "color": color,
                          "size": size, "meta": meta})

    def add_edge(src, tgt, label):
        edges.append({"source": src, "target": tgt, "label": label})

    victim_nid = f"victim_{victim_id}"
    add_node(victim_nid, v.full_name, "Victim", "#ff4d5e", 14,
             f"Victim · {v.district or 'Unknown'}")

    case_ids = [cv.case_id for cv in db.query(m.CaseVictim).filter(
        m.CaseVictim.victim_id == victim_id).all()]
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
            add_node(wnid, w.name, "Witness", "#24d18b", 7,
                     f"Reliability: {w.reliability}")
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

    if v.address:
        short_addr = v.address[:30]
        addr_key = v.address.strip().lower()[:40]
        vaddr_nid = f"addr_{hash(addr_key) % 100000}"
        already_exists = vaddr_nid in seen
        add_node(vaddr_nid, short_addr, "Address", "#888", 6, v.address)
        add_edge(victim_nid, vaddr_nid, "Lives At")
        if already_exists:
            for e in edges:
                if e["source"] != victim_nid and e["target"] == vaddr_nid and e["label"] == "Lives At":
                    add_edge(victim_nid, e["source"], "Lives Together")
                    break

    return {"nodes": nodes, "edges": edges}
