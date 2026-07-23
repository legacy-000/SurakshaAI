"""Alerts / early-warning feed."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(db: Session = Depends(get_db), unresolved_only: bool = False):
    q = db.query(m.Alert)
    if unresolved_only:
        q = q.filter(m.Alert.resolved.is_(False))
    rows = q.order_by(m.Alert.created_at.desc()).all()
    return [{"id": a.id, "title": a.title, "message": a.message, "severity": a.severity,
             "alert_type": a.alert_type, "district": a.district, "is_read": a.is_read,
             "resolved": a.resolved, "created_at": a.created_at.isoformat()} for a in rows]


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(m.Alert, alert_id)
    if not a:
        raise HTTPException(404, "alert not found")
    a.resolved = True
    a.is_read = True
    db.commit()
    return {"ok": True}
