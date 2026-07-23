"""Audit trail viewer (governance / accountability)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/logs")
def logs(request: Request, db: Session = Depends(get_db),
         limit: int = 100, role: str | None = None, pii_only: bool = False):
    ctx = get_ctx(request)
    if not ctx.caps["can_view_audit"]:
        raise HTTPException(403, "Your role cannot view audit logs.")
    q = db.query(m.AuditLog)
    if role:
        q = q.filter(m.AuditLog.role == role)
    if pii_only:
        q = q.filter(m.AuditLog.pii_accessed.is_(True))
    rows = q.order_by(m.AuditLog.created_at.desc()).limit(limit).all()
    return [{"id": a.id, "user_name": a.user_name, "role": a.role, "action": a.action,
             "path": a.path, "resource": a.resource, "status_code": a.status_code,
             "pii_accessed": a.pii_accessed, "created_at": a.created_at.isoformat()}
            for a in rows]


@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if not ctx.caps["can_view_audit"]:
        raise HTTPException(403, "Your role cannot view audit logs.")
    total = db.query(func.count(m.AuditLog.id)).scalar() or 0
    pii = db.query(func.count(m.AuditLog.id)).filter(m.AuditLog.pii_accessed.is_(True)).scalar() or 0
    by_role = (db.query(m.AuditLog.role, func.count(m.AuditLog.id))
               .group_by(m.AuditLog.role).all())
    by_resource = (db.query(m.AuditLog.resource, func.count(m.AuditLog.id))
                   .group_by(m.AuditLog.resource)
                   .order_by(func.count(m.AuditLog.id).desc()).limit(8).all())
    return {"total": total, "pii_accesses": pii,
            "by_role": [{"label": r[0], "value": r[1]} for r in by_role],
            "by_resource": [{"label": r[0], "value": r[1]} for r in by_resource]}
