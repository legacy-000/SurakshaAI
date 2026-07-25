"""Alerts / early-warning feed."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db), unresolved_only: bool = False):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        where = "WHERE resolved = false" if unresolved_only else ""
        rows = store.query(f"SELECT * FROM alerts {where} ORDER BY CREATEDTIME DESC")
        return [{"id": a.get("ROWID"), "title": a.get("title"), "message": a.get("message"),
                 "severity": a.get("severity"), "alert_type": a.get("alert_type"),
                 "district": a.get("district"), "is_read": a.get("is_read"),
                 "resolved": a.get("resolved"),
                 "created_at": a.get("CREATEDTIME")} for a in rows]

    q = db.query(m.Alert)
    if unresolved_only:
        q = q.filter(m.Alert.resolved.is_(False))
    rows = q.order_by(m.Alert.created_at.desc()).all()
    return [{"id": a.id, "title": a.title, "message": a.message, "severity": a.severity,
             "alert_type": a.alert_type, "district": a.district, "is_read": a.is_read,
             "resolved": a.resolved, "created_at": a.created_at.isoformat()} for a in rows]


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        a = store.get("alerts", alert_id)
        if not a:
            raise HTTPException(404, "alert not found")
        store.update("alerts", alert_id, {"resolved": True, "is_read": True})
        return {"ok": True}

    a = db.get(m.Alert, alert_id)
    if not a:
        raise HTTPException(404, "alert not found")
    a.resolved = True
    a.is_read = True
    db.commit()
    return {"ok": True}
