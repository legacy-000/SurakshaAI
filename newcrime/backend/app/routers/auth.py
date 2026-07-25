"""Lightweight demo auth + RBAC (local only, not production-grade)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..schemas import LoginRequest
from ..deps import ROLE_MATRIX
from .. import models as m

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        rows = store.query(f"SELECT * FROM users WHERE username = '{req.username}'")
        if not rows or rows[0].get("password") != req.password:
            raise HTTPException(401, "invalid credentials")
        return _user_payload_dict(rows[0])

    user = db.query(m.User).filter(m.User.username == req.username).first()
    if not user or user.password != req.password:
        raise HTTPException(401, "invalid credentials")
    return _user_payload(user)


@router.get("/users")
def demo_users(db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        rows = store.query("SELECT * FROM users")
        return [{"username": u.get("username"), "full_name": u.get("full_name"),
                 "role": u.get("role"),
                 "rank": ROLE_MATRIX.get(u.get("role"), {}).get("rank", u.get("role")),
                 "badge": u.get("badge_number")} for u in rows]

    users = db.query(m.User).all()
    return [{"username": u.username, "full_name": u.full_name, "role": u.role,
             "rank": ROLE_MATRIX.get(u.role, {}).get("rank", u.role),
             "badge": u.badge_number} for u in users]


def _user_payload(user: m.User):
    caps = ROLE_MATRIX.get(user.role, ROLE_MATRIX["sub_inspector"])
    return {"id": user.id, "username": user.username, "full_name": user.full_name,
            "role": user.role, "rank": caps["rank"], "badge_number": user.badge_number,
            "district": user.district,
            "subdivision": getattr(user, 'subdivision', None) or "",
            "range_name": getattr(user, 'range_name', None) or "",
            "station": getattr(user, 'station', None) or "",
            "permissions": {"screens": caps["screens"],
                            "can_view_pii": caps["can_view_pii"],
                            "can_view_sql": caps["can_view_sql"],
                            "can_export": caps["can_export"],
                            "can_view_audit": caps["can_view_audit"],
                            "can_investigate": caps.get("can_investigate", False),
                            "scope": caps["scope"],
                            "command_level": caps.get("command_level")}}


def _user_payload_dict(u: dict):
    role = u.get("role", "sub_inspector")
    caps = ROLE_MATRIX.get(role, ROLE_MATRIX["sub_inspector"])
    return {"id": u.get("ROWID"), "username": u.get("username"),
            "full_name": u.get("full_name"), "role": role,
            "rank": caps["rank"], "badge_number": u.get("badge_number"),
            "district": u.get("district"),
            "subdivision": u.get("subdivision") or "",
            "range_name": u.get("range_name") or "",
            "station": u.get("station") or "",
            "permissions": {"screens": caps["screens"],
                            "can_view_pii": caps["can_view_pii"],
                            "can_view_sql": caps["can_view_sql"],
                            "can_export": caps["can_export"],
                            "can_view_audit": caps["can_view_audit"],
                            "can_investigate": caps.get("can_investigate", False),
                            "scope": caps["scope"],
                            "command_level": caps.get("command_level")}}
