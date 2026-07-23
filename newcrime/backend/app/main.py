"""FastAPI entry point for the Crime Intelligence Platform (local)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine, SessionLocal
from . import models  # noqa: F401  (register tables)
from .llm import get_llm
from .routers import (
    auth, cases, chat, analytics, network, profiling, socio, forecasting,
    financial, alerts, audit, dashboards, investigation,
)
from .deps import get_ctx


def _ensure_seeded():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        empty = db.query(models.Case).first() is None
    finally:
        db.close()
    if empty:
        from .seed import seed
        print("[startup] empty database detected — seeding synthetic data...")
        seed()
        print("[startup] seed complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ensure_seeded()
    yield


app = FastAPI(title="Crime Intelligence Platform", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, chat, cases, analytics, network, profiling, socio, forecasting,
          financial, alerts, audit, dashboards, investigation):
    app.include_router(r.router)


# ── Audit middleware: records every meaningful API access ─────────────
_RESOURCE_MAP = {
    "chat": "AI Assistant", "cases": "Case/FIR", "analytics": "Analytics",
    "network": "Criminal Network", "profiling": "Offender Profiling",
    "socio": "Socio Insights", "forecasting": "Forecasting",
    "financial": "Financial Crime", "alerts": "Alerts", "auth": "Auth",
    "investigation": "Investigation", "workspace": "Workspace", "command": "Command Center",
}
_PII_RESOURCES = {"cases", "profiling", "chat", "financial", "investigation"}


@app.middleware("http")
async def audit_mw(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if (request.method == "OPTIONS" or not path.startswith("/api")
            or path.startswith("/api/audit") or path == "/api/health"):
        return response
    try:
        ctx = get_ctx(request)
        seg = path.split("/")
        key = seg[2] if len(seg) > 2 else ""
        pii = key in _PII_RESOURCES and ctx.can_view_pii and request.method == "GET"
        db = SessionLocal()
        try:
            db.add(models.AuditLog(
                user_id=ctx.user_id, user_name=ctx.name, role=ctx.role,
                action=request.method, path=path,
                resource=_RESOURCE_MAP.get(key, key or "root"),
                status_code=response.status_code, pii_accessed=pii))
            db.commit()
        finally:
            db.close()
    except Exception:
        pass
    return response


@app.get("/api/health")
def health():
    llm = get_llm()
    return {"status": "ok",
            "llm_provider": llm.provider,
            "llm_configured": llm.provider != "mock",
            "note": "Running on mock LLM fallback." if llm.provider == "mock"
                    else f"Using {llm.provider} provider."}


@app.get("/")
def root():
    return {"name": "Crime Intelligence Platform API",
            "docs": "/docs", "health": "/api/health"}
