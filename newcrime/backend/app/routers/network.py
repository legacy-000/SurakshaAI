"""Criminal network & relationship analysis."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/graph")
def graph(db: Session = Depends(get_db), gang: str | None = None, min_degree: int = 0):
    """Return nodes (accused) + edges (associations) for the graph view."""
    q = db.query(m.Association)
    if gang:
        q = q.filter(m.Association.gang_name == gang)
    assocs = q.all()

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
    rows = (db.query(m.Association.gang_name, func.count(m.Association.id))
            .filter(m.Association.gang_name.isnot(None))
            .group_by(m.Association.gang_name)
            .order_by(func.count(m.Association.id).desc()).all())
    return [{"name": r[0], "links": r[1]} for r in rows]


@router.get("/accused/{accused_id}")
def ego_network(accused_id: int, db: Session = Depends(get_db)):
    """Direct associates of one accused."""
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
