"""Lightweight demo auth + RBAC (local only, not production-grade).

Returns the officer's rank + permission matrix the frontend uses to gate
screens, mask PII and toggle SQL/audit visibility. No real tokens/hashing —
this is a local prototype.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import LoginRequest
from ..deps import ROLE_MATRIX
from .. import models as m

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(m.User).filter(m.User.username == req.username).first()
    if not user or user.password != req.password:
        raise HTTPException(401, "invalid credentials")
    return _user_payload(user)


@router.get("/users")
def demo_users(db: Session = Depends(get_db)):
    """List demo accounts (local prototype convenience)."""
    users = db.query(m.User).all()
    return [{"username": u.username, "full_name": u.full_name, "role": u.role,
             "rank": ROLE_MATRIX.get(u.role, {}).get("rank", u.role),
             "badge": u.badge_number} for u in users]


def _user_payload(user: m.User):
    caps = ROLE_MATRIX.get(user.role, ROLE_MATRIX["sub_inspector"])
    return {"id": user.id, "username": user.username, "full_name": user.full_name,
            "role": user.role, "rank": caps["rank"], "badge_number": user.badge_number,
            "district": user.district,
            "permissions": {"screens": caps["screens"],
                            "can_view_pii": caps["can_view_pii"],
                            "can_view_sql": caps["can_view_sql"],
                            "can_export": caps["can_export"],
                            "can_view_audit": caps["can_view_audit"],
                            "can_investigate": caps.get("can_investigate", False),
                            "scope": caps["scope"]}}
