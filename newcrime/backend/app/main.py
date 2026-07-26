"""FastAPI entry point for the Crime Intelligence Platform."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine, SessionLocal, migrate, get_engine
from .llm import get_llm
from .routers import (
    auth, cases, chat, analytics, network, profiling, socio, forecasting,
    financial, alerts, audit, dashboards, investigation, victims,
)
from .deps import get_ctx


def _ensure_seeded():
    from . import models  # noqa: F401  (register tables)
    real_engine = get_engine()
    Base.metadata.create_all(bind=real_engine)
    migrate(real_engine)
    db = SessionLocal()
    try:
        empty = db.query(models.User).first() is None or db.query(models.Case).first() is None
    except Exception:
        empty = True
    finally:
        db.close()
    if empty:
        from .seed import seed
        print("[startup] empty database detected — seeding synthetic data...")
        seed()
        print("[startup] seed complete.")


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    if settings.use_catalyst:
        from .catalyst_store import init_catalyst_store
        init_catalyst_store()
    else:
        _ensure_seeded()
    yield


def create_app() -> FastAPI:
    """Factory used by the Catalyst function adapter and for testing."""
    application = FastAPI(title="Crime Intelligence Platform", version="1.0.0",
                          lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for r in (auth, chat, cases, analytics, network, profiling, socio, forecasting,
              financial, alerts, audit, dashboards, investigation, victims):
        application.include_router(r.router)
    application.middleware("http")(audit_mw)
    application.get("/api/health")(health)
    application.get("/")(root)
    return application


# ── Audit middleware: records every meaningful API access ─────────────
_RESOURCE_MAP = {
    "chat": "AI Assistant", "cases": "Case/FIR", "analytics": "Analytics",
    "network": "Criminal Network", "profiling": "Offender Profiling",
    "socio": "Socio Insights", "forecasting": "Forecasting",
    "financial": "Financial Crime", "alerts": "Alerts", "auth": "Auth",
    "investigation": "Investigation", "workspace": "Workspace", "command": "Command Center",
}
_PII_RESOURCES = {"cases", "profiling", "chat", "financial", "investigation"}


_METHOD_ACTION = {"GET": "view", "POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}


def _classify_action(method: str, path: str) -> str:
    if "/login" in path:
        return "login"
    if "/evidence" in path and method == "POST":
        return "upload"
    if "/approval" in path or "/review" in path:
        return "approve" if method == "POST" else "view"
    if "/stage/request" in path:
        return "approve"
    if "/briefing" in path or "/chargesheet" in path:
        return "export" if method == "POST" else "view"
    return _METHOD_ACTION.get(method, "view")


async def audit_mw(request, call_next):
    path = request.url.path
    if (request.method == "OPTIONS" or not path.startswith("/api")
            or path.startswith("/api/audit") or path == "/api/health"):
        return await call_next(request)

    body_text = None
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        content_type = request.headers.get("content-type", "")
        if "json" in content_type:
            try:
                raw = await request.body()
                body_text = raw.decode("utf-8", errors="replace")[:2000]
            except Exception:
                pass
        elif "form" in content_type and "multipart" not in content_type:
            try:
                raw = await request.body()
                body_text = raw.decode("utf-8", errors="replace")[:2000]
            except Exception:
                pass

    response = await call_next(request)
    try:
        ctx = get_ctx(request)
        seg = path.split("/")
        key = seg[2] if len(seg) > 2 else ""
        pii = key in _PII_RESOURCES and ctx.can_view_pii and request.method == "GET"

        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not ip:
            ip = request.client.host if request.client else "unknown"
        ua = request.headers.get("user-agent", "")[:255]
        sid = request.headers.get("x-session-id", "")

        action_type = _classify_action(request.method, path)

        resource_name = _RESOURCE_MAP.get(key, key or "root")
        detail_parts = [f"{request.method} {path}"]
        if response.status_code >= 400:
            detail_parts.append(f"status={response.status_code}")
        detail = " | ".join(detail_parts)

        new_value = body_text if action_type in ("create", "update") else None

        if settings.use_catalyst:
            from .catalyst_store import get_store
            try:
                store = get_store()
                store.insert("audit_logs", {
                    "user_id": ctx.user_id, "user_name": ctx.name, "role": ctx.role,
                    "path": path, "resource": resource_name,
                    "status_code": response.status_code, "pii_accessed": pii,
                    "action_type": action_type, "detail": detail,
                    "ip_address": ip, "user_agent": ua, "session_id": sid,
                    "district": ctx.district, "new_value": new_value,
                })
            except Exception:
                pass
        else:
            from . import models
            db = SessionLocal()
            try:
                db.add(models.AuditLog(
                    user_id=ctx.user_id, user_name=ctx.name, role=ctx.role,
                    action=request.method, path=path,
                    resource=resource_name,
                    status_code=response.status_code, pii_accessed=pii,
                    action_type=action_type, detail=detail,
                    ip_address=ip, user_agent=ua, session_id=sid,
                    district=ctx.district, new_value=new_value))
                db.commit()
            finally:
                db.close()
    except Exception:
        pass
    return response


def _forecast_error():
    from .services import forecast
    return forecast.last_error


def _datastore_error():
    if not settings.use_catalyst:
        return None
    try:
        from .catalyst_store import get_store
        return get_store().last_error
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def _filestore_state():
    from .services import file_store
    return {"folders_configured": sum(bool(x) for x in (
                settings.evidence_folder_id, settings.witness_folder_id,
                settings.chat_uploads_folder_id)),
            "last_error": file_store.last_error}


def health():
    llm = get_llm()
    try:
        import zcatalyst_sdk  # noqa: F401
        sdk = "importable"
    except Exception as e:
        sdk = f"unavailable ({type(e).__name__})"
    return {"status": "ok",
            "llm_provider": llm.provider,
            "llm_configured": llm.provider != "mock",
            "configured_provider": settings.llm_provider,
            "glm_model_id": settings.glm_model_id or None,
            "glm_endpoint": settings.glm_endpoint_url or None,
            "zcatalyst_sdk": sdk,
            "llm_last_error": getattr(llm, "last_error", None),
            "quickml_endpoint": bool(settings.quickml_endpoint_key),
            "forecast_last_error": _forecast_error(),
            "file_store": _filestore_state(),
            "datastore_last_error": _datastore_error(),
            "note": "Running on mock LLM fallback." if llm.provider == "mock"
                    else f"Using {llm.provider} provider."}


def root():
    return {"name": "Crime Intelligence Platform API",
            "docs": "/docs", "health": "/api/health"}


app = create_app()
