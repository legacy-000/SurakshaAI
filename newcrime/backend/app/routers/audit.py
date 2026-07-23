"""Audit trail viewer (governance / accountability) with territory-based scoping."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _scope_query(q, ctx):
    """Apply territory-based WHERE clause so officers only see audit logs from their scope."""
    if ctx.scope == "state":
        return q
    allowed = ctx.districts_in_scope()
    if not allowed:
        return q.filter(or_(m.AuditLog.district.is_(None), m.AuditLog.district == ""))
    return q.filter(or_(
        m.AuditLog.district.in_(allowed),
        m.AuditLog.district.is_(None),
        m.AuditLog.district == "",
    ))


@router.get("/logs")
def logs(request: Request, db: Session = Depends(get_db),
         limit: int = 100, role: str | None = None, pii_only: bool = False,
         action_type: str | None = None, resource: str | None = None,
         district: str | None = None, user_name: str | None = None):
    ctx = get_ctx(request)
    if not ctx.caps["can_view_audit"]:
        raise HTTPException(403, "Your role cannot view audit logs.")
    q = _scope_query(db.query(m.AuditLog), ctx)
    if role:
        q = q.filter(m.AuditLog.role == role)
    if pii_only:
        q = q.filter(m.AuditLog.pii_accessed.is_(True))
    if action_type:
        q = q.filter(m.AuditLog.action_type == action_type)
    if resource:
        q = q.filter(m.AuditLog.resource == resource)
    if district:
        q = q.filter(m.AuditLog.district == district)
    if user_name:
        q = q.filter(m.AuditLog.user_name.ilike(f"%{user_name}%"))
    rows = q.order_by(m.AuditLog.created_at.desc()).limit(limit).all()
    return [{"id": a.id, "user_name": a.user_name, "role": a.role, "action": a.action,
             "path": a.path, "resource": a.resource, "status_code": a.status_code,
             "pii_accessed": a.pii_accessed, "created_at": a.created_at.isoformat(),
             "action_type": a.action_type, "detail": a.detail,
             "ip_address": a.ip_address, "user_agent": a.user_agent,
             "session_id": a.session_id, "district": a.district,
             "prev_value": a.prev_value, "new_value": a.new_value}
            for a in rows]


@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if not ctx.caps["can_view_audit"]:
        raise HTTPException(403, "Your role cannot view audit logs.")
    q = _scope_query(db.query(m.AuditLog), ctx)
    total = q.count()
    pii = q.filter(m.AuditLog.pii_accessed.is_(True)).count()
    by_role = (q.with_entities(m.AuditLog.role, func.count(m.AuditLog.id))
               .group_by(m.AuditLog.role).all())
    by_resource = (q.with_entities(m.AuditLog.resource, func.count(m.AuditLog.id))
                   .group_by(m.AuditLog.resource)
                   .order_by(func.count(m.AuditLog.id).desc()).limit(8).all())
    by_action_type = (q.with_entities(m.AuditLog.action_type, func.count(m.AuditLog.id))
                      .filter(m.AuditLog.action_type.isnot(None))
                      .group_by(m.AuditLog.action_type).all())
    by_district = (q.with_entities(m.AuditLog.district, func.count(m.AuditLog.id))
                   .filter(m.AuditLog.district.isnot(None), m.AuditLog.district != "")
                   .group_by(m.AuditLog.district)
                   .order_by(func.count(m.AuditLog.id).desc()).limit(10).all())
    return {"total": total, "pii_accesses": pii,
            "scope": ctx.scope, "scope_districts": ctx.districts_in_scope(),
            "by_role": [{"label": r[0], "value": r[1]} for r in by_role],
            "by_resource": [{"label": r[0], "value": r[1]} for r in by_resource],
            "by_action_type": [{"label": r[0] or "unknown", "value": r[1]} for r in by_action_type],
            "by_district": [{"label": r[0], "value": r[1]} for r in by_district]}
