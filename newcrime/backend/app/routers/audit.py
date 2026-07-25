"""Audit trail viewer (governance / accountability) with territory-based scoping."""
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api/audit", tags=["audit"])


def _scope_query(q, ctx):
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


def _scope_rows(rows: list[dict], ctx) -> list[dict]:
    if ctx.scope == "state":
        return rows
    allowed = set(ctx.districts_in_scope())
    if not allowed:
        return [r for r in rows if not r.get("district")]
    return [r for r in rows if r.get("district") in allowed or not r.get("district")]


@router.get("/logs")
def logs(request: Request, db: Session = Depends(get_db),
         limit: int = 100, role: str | None = None, pii_only: bool = False,
         action_type: str | None = None, resource: str | None = None,
         district: str | None = None, user_name: str | None = None):
    ctx = get_ctx(request)
    if not ctx.caps["can_view_audit"]:
        raise HTTPException(403, "Your role cannot view audit logs.")

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        rows = store.query("SELECT * FROM audit_logs ORDER BY CREATEDTIME DESC")
        rows = _scope_rows(rows, ctx)
        if role:
            rows = [r for r in rows if r.get("role") == role]
        if pii_only:
            rows = [r for r in rows if r.get("pii_accessed")]
        if action_type:
            rows = [r for r in rows if r.get("action_type") == action_type]
        if resource:
            rows = [r for r in rows if r.get("resource") == resource]
        if district:
            rows = [r for r in rows if r.get("district") == district]
        if user_name:
            rows = [r for r in rows if user_name.lower() in (r.get("user_name") or "").lower()]
        rows = rows[:limit]
        return [{"id": a.get("ROWID"), "user_name": a.get("user_name"), "role": a.get("role"),
                 "action": a.get("action"), "path": a.get("path"), "resource": a.get("resource"),
                 "status_code": a.get("status_code"), "pii_accessed": a.get("pii_accessed"),
                 "created_at": a.get("CREATEDTIME"), "action_type": a.get("action_type"),
                 "detail": a.get("detail"), "ip_address": a.get("ip_address"),
                 "user_agent": a.get("user_agent"), "session_id": a.get("session_id"),
                 "district": a.get("district"), "prev_value": a.get("prev_value"),
                 "new_value": a.get("new_value")} for a in rows]

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

    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        all_rows = store.query("SELECT * FROM audit_logs")
        all_rows = _scope_rows(all_rows, ctx)
        total = len(all_rows)
        pii = sum(1 for r in all_rows if r.get("pii_accessed"))
        by_role = Counter(r.get("role") for r in all_rows)
        by_resource = Counter(r.get("resource") for r in all_rows).most_common(8)
        by_action_type = Counter(r.get("action_type") for r in all_rows if r.get("action_type"))
        by_district = Counter(r.get("district") for r in all_rows
                              if r.get("district"))
        by_district_top = by_district.most_common(10)
        return {"total": total, "pii_accesses": pii,
                "scope": ctx.scope, "scope_districts": ctx.districts_in_scope(),
                "by_role": [{"label": k, "value": v} for k, v in by_role.items()],
                "by_resource": [{"label": k, "value": v} for k, v in by_resource],
                "by_action_type": [{"label": k or "unknown", "value": v} for k, v in by_action_type.items()],
                "by_district": [{"label": k, "value": v} for k, v in by_district_top]}

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
