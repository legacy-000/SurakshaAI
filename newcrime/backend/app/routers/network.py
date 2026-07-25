"""Criminal network & relationship analysis."""
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/graph")
def graph(db: Session = Depends(get_db), gang: str | None = None, min_degree: int = 0):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        where = f" WHERE gang_name = '{gang}'" if gang else ""
        assocs = store.query(f"SELECT * FROM associations{where}")
        degree: dict = {}
        for a in assocs:
            sid = a.get("source_accused_id") or a.get("source_id")
            tid = a.get("target_accused_id") or a.get("target_id")
            degree[sid] = degree.get(sid, 0) + 1
            degree[tid] = degree.get(tid, 0) + 1
        node_ids = {nid for nid, d in degree.items() if d >= min_degree}
        if not node_ids:
            return {"nodes": [], "edges": []}
        all_accused = store.query("SELECT * FROM accused")
        profiles = store.query("SELECT * FROM behavior_profiles")
        prof_map = {p.get("accused_id"): p for p in profiles}
        nodes = []
        for a in all_accused:
            rid = a.get("ROWID")
            if rid not in node_ids:
                continue
            p = prof_map.get(rid, {})
            nodes.append({"id": rid, "label": a.get("full_name"), "district": a.get("district"),
                          "status": a.get("status"), "degree": degree.get(rid, 0),
                          "risk": round(float(p.get("risk_score", 0))),
                          "band": p.get("risk_band", "Low")})
        edges = []
        for a in assocs:
            sid = a.get("source_accused_id") or a.get("source_id")
            tid = a.get("target_accused_id") or a.get("target_id")
            if sid in node_ids and tid in node_ids:
                edges.append({"source": sid, "target": tid,
                              "type": a.get("relationship_type"), "gang": a.get("gang_name"),
                              "strength": a.get("strength")})
        return {"nodes": nodes, "edges": edges}

    assocs = db.query(m.Association)
    if gang:
        assocs = assocs.filter(m.Association.gang_name == gang)
    assocs = assocs.all()
    degree: dict[int, int] = {}
    for a in assocs:
        degree[a.source_accused_id] = degree.get(a.source_accused_id, 0) + 1
        degree[a.target_accused_id] = degree.get(a.target_accused_id, 0) + 1
    node_ids = {nid for nid, d in degree.items() if d >= min_degree}
    accused = db.query(m.Accused).filter(m.Accused.id.in_(node_ids)).all() if node_ids else []
    profiles = {p.accused_id: p for p in db.query(m.BehaviorProfile)
                .filter(m.BehaviorProfile.accused_id.in_(node_ids)).all()}
    nodes = [{"id": a.id, "label": a.full_name, "district": a.district,
              "status": a.status, "degree": degree.get(a.id, 0),
              "risk": round(profiles[a.id].risk_score) if a.id in profiles else 0,
              "band": profiles[a.id].risk_band if a.id in profiles else "Low"}
             for a in accused]
    edges = [{"source": a.source_accused_id, "target": a.target_accused_id,
              "type": a.relationship_type, "gang": a.gang_name, "strength": a.strength}
             for a in assocs
             if a.source_accused_id in node_ids and a.target_accused_id in node_ids]
    return {"nodes": nodes, "edges": edges}


@router.get("/gangs")
def gangs(db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        counts = store.aggregate("associations", "gang_name",
                                 "gang_name IS NOT NULL")
        return sorted([{"name": k, "links": v} for k, v in counts.items()],
                      key=lambda x: -x["links"])

    rows = (db.query(m.Association.gang_name, func.count(m.Association.id))
            .filter(m.Association.gang_name.isnot(None))
            .group_by(m.Association.gang_name)
            .order_by(func.count(m.Association.id).desc()).all())
    return [{"name": r[0], "links": r[1]} for r in rows]


@router.get("/accused/{accused_id}")
def ego_network(accused_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        a = store.get("accused", accused_id)
        if not a:
            raise HTTPException(404, "accused not found")
        assocs = store.query(
            f"SELECT * FROM associations WHERE source_accused_id = {accused_id} "
            f"OR target_accused_id = {accused_id}")
        associate_ids = set()
        for x in assocs:
            sid = x.get("source_accused_id") or x.get("source_id")
            tid = x.get("target_accused_id") or x.get("target_id")
            associate_ids.add(tid if sid == accused_id else sid)
        all_accused = store.query("SELECT * FROM accused")
        associates = [x for x in all_accused if x.get("ROWID") in associate_ids]
        return {"accused": {"id": accused_id, "name": a.get("full_name"),
                            "district": a.get("district")},
                "associates": [{"id": x.get("ROWID"), "name": x.get("full_name"),
                                "district": x.get("district"), "status": x.get("status")}
                               for x in associates],
                "links": [{"source": x.get("source_accused_id") or x.get("source_id"),
                           "target": x.get("target_accused_id") or x.get("target_id"),
                           "type": x.get("relationship_type"), "gang": x.get("gang_name")}
                          for x in assocs]}

    a = db.get(m.Accused, accused_id)
    if not a:
        raise HTTPException(404, "accused not found")
    assocs = (db.query(m.Association)
              .filter(or_(m.Association.source_accused_id == accused_id,
                          m.Association.target_accused_id == accused_id)).all())
    associate_ids = {x.target_accused_id if x.source_accused_id == accused_id
                     else x.source_accused_id for x in assocs}
    associates = db.query(m.Accused).filter(m.Accused.id.in_(associate_ids)).all()
    return {"accused": {"id": a.id, "name": a.full_name, "district": a.district},
            "associates": [{"id": x.id, "name": x.full_name, "district": x.district,
                            "status": x.status} for x in associates],
            "links": [{"source": e.source_accused_id, "target": e.target_accused_id,
                       "type": e.relationship_type, "gang": e.gang_name} for e in assocs]}
