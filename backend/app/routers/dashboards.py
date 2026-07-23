"""Role-scoped Workspace + strategic Command Center dashboards."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api", tags=["dashboards"])

COMMAND_ROLES = {"sho", "dsp", "commander"}


def _scope(q, ctx, col):
    df = ctx.district_filter()
    if df:
        return q.filter(col == df)
    return q


# ── Workspace (personal home, all roles) ──────────────────────────────
@router.get("/workspace/overview")
def workspace(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    df = ctx.district_filter()

    def cases_q():
        return _scope(db.query(m.Case), ctx, m.Case.district)

    open_cases = cases_q().filter(m.Case.status.in_(["Open", "Under Investigation"])).count()
    needs_action = cases_q().filter(m.Case.status == "Open").count()
    since = datetime.utcnow() - timedelta(days=30)
    arrests = (db.query(func.count(m.TimelineEvent.id))
               .join(m.Case, m.Case.id == m.TimelineEvent.case_id)
               .filter(m.TimelineEvent.event_type == "Arrest")
               .filter(m.TimelineEvent.event_timestamp >= since))
    if df:
        arrests = arrests.filter(m.Case.district == df)
    arrests = arrests.scalar() or 0
    alerts_q = db.query(m.Alert).filter(m.Alert.resolved.is_(False))
    if df:
        alerts_q = alerts_q.filter(m.Alert.district == df)
    my_alerts = alerts_q.count()

    # role-specific KPI set
    role = ctx.role
    if role == "analyst":
        kpis = [
            {"label": "Detected Patterns", "value": db.query(func.count(m.CrimePattern.id)).scalar() or 0},
            {"label": "Active Forecasts", "value": db.query(func.count(m.Prediction.id)).scalar() or 0},
            {"label": "High-risk Offenders", "value": db.query(func.count(m.BehaviorProfile.id))
                .filter(m.BehaviorProfile.risk_band.in_(["High", "Critical"])).scalar() or 0, "accent": "#ff4d5e"},
            {"label": "Open Alerts", "value": my_alerts, "accent": "#ffb020"},
        ]
    elif role in ("dsp", "commander"):
        total = cases_q().count() or 1
        solved = cases_q().filter(m.Case.status.in_(["Chargesheeted", "Closed"])).count()
        kpis = [
            {"label": "Cases in Jurisdiction", "value": cases_q().count()},
            {"label": "Clearance Rate", "value": f"{round(solved/total*100,1)}%", "accent": "#24d18b"},
            {"label": "High-risk Offenders", "value": db.query(func.count(m.BehaviorProfile.id))
                .filter(m.BehaviorProfile.risk_band.in_(["High", "Critical"])).scalar() or 0, "accent": "#ff4d5e"},
            {"label": "Active Alerts", "value": my_alerts, "accent": "#ffb020"},
        ]
    else:  # constable / sub_inspector / sho
        kpis = [
            {"label": "Open Cases", "value": open_cases},
            {"label": "Needs Action", "value": needs_action, "accent": "#ffb020"},
            {"label": "Arrests (30d)", "value": arrests, "accent": "#24d18b"},
            {"label": "My Alerts", "value": my_alerts, "accent": "#ff4d5e"},
        ]

    my_cases = (cases_q().order_by(m.Case.occurrence_date.desc()).limit(8).all())
    # intelligence stream: recent events in scope
    ev_q = (db.query(m.TimelineEvent, m.Case)
            .join(m.Case, m.Case.id == m.TimelineEvent.case_id)
            .order_by(m.TimelineEvent.event_timestamp.desc()))
    if df:
        ev_q = ev_q.filter(m.Case.district == df)
    stream = [{"title": e.event_title, "type": e.event_type,
               "case": c.fir_number, "district": c.district,
               "time": e.event_timestamp.isoformat() if e.event_timestamp else None}
              for e, c in ev_q.limit(8).all()]

    return {
        "officer": {"name": ctx.name, "role": role, "rank": ctx.caps["rank"],
                    "scope": ctx.scope, "district": df or "All districts"},
        "kpis": kpis,
        "my_cases": [{"id": c.id, "fir_number": c.fir_number, "title": c.title,
                      "crime_type": c.crime_type, "status": c.status, "severity": c.severity,
                      "district": c.district} for c in my_cases],
        "stream": stream,
        "can_command": role in COMMAND_ROLES,
    }


# ── Command Center (strategic, senior roles) ──────────────────────────
@router.get("/command/overview")
def command(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if ctx.role not in COMMAND_ROLES:
        raise HTTPException(403, "Command Center is restricted to SHO / DSP / Commander.")
    df = ctx.district_filter()

    def cases_q():
        return _scope(db.query(m.Case), ctx, m.Case.district)

    total = cases_q().count() or 1
    by_status = dict(_scope(db.query(m.Case.status, func.count(m.Case.id)), ctx, m.Case.district)
                     .group_by(m.Case.status).all())
    solved = by_status.get("Chargesheeted", 0) + by_status.get("Closed", 0)
    now = datetime.utcnow()
    this_month = cases_q().filter(m.Case.occurrence_date >= now - timedelta(days=30)).count()
    last_month = cases_q().filter(m.Case.occurrence_date >= now - timedelta(days=60),
                                  m.Case.occurrence_date < now - timedelta(days=30)).count()
    since = now - timedelta(days=30)
    arrests_q = (db.query(func.count(m.TimelineEvent.id))
                 .join(m.Case, m.Case.id == m.TimelineEvent.case_id)
                 .filter(m.TimelineEvent.event_type == "Arrest",
                         m.TimelineEvent.event_timestamp >= since))
    if df:
        arrests_q = arrests_q.filter(m.Case.district == df)

    kpis = {
        "total_cases": cases_q().count(),
        "open": by_status.get("Open", 0) + by_status.get("Under Investigation", 0),
        "clearance_rate": round(solved / total * 100, 1),
        "firs_this_month": this_month,
        "firs_change": round((this_month - last_month) / last_month * 100, 1) if last_month else 0,
        "arrests_month": arrests_q.scalar() or 0,
        "by_status": [{"label": k, "value": v} for k, v in by_status.items()],
    }

    # intelligence stream
    ev_q = (db.query(m.TimelineEvent, m.Case)
            .join(m.Case, m.Case.id == m.TimelineEvent.case_id)
            .order_by(m.TimelineEvent.event_timestamp.desc()))
    if df:
        ev_q = ev_q.filter(m.Case.district == df)
    stream = [{"title": e.event_title, "type": e.event_type, "case": c.fir_number,
               "district": c.district, "severity": c.severity,
               "time": e.event_timestamp.isoformat() if e.event_timestamp else None}
              for e, c in ev_q.limit(10).all()]

    # priority alerts
    al_q = db.query(m.Alert).filter(m.Alert.resolved.is_(False))
    if df:
        al_q = al_q.filter(m.Alert.district == df)
    alerts = [{"id": a.id, "title": a.title, "severity": a.severity, "type": a.alert_type,
               "district": a.district} for a in
              al_q.order_by(m.Alert.created_at.desc()).limit(6).all()]

    # top high-risk offenders
    off = (db.query(m.Accused, m.BehaviorProfile)
           .join(m.BehaviorProfile, m.BehaviorProfile.accused_id == m.Accused.id))
    if df:
        off = off.filter(m.Accused.district == df)
    off = off.order_by(m.BehaviorProfile.risk_score.desc()).limit(6).all()
    offenders = [{"id": a.id, "name": (a.full_name if ctx.can_view_pii else a.full_name[0] + "•••••"),
                  "district": a.district, "risk": round(p.risk_score), "band": p.risk_band}
                 for a, p in off]

    # predicted hotspots
    pred_q = db.query(m.Prediction).order_by(m.Prediction.probability.desc())
    if df:
        pred_q = pred_q.filter(m.Prediction.target_area == df)
    preds = pred_q.limit(6).all()
    predictions = [{"area": p.target_area, "crime": p.crime_type, "prob": p.probability,
                    "level": p.risk_level} for p in preds]

    # district comparison (state/district roles)
    dist_rows = (_scope(db.query(m.Case.district, func.count(m.Case.id)), ctx, m.Case.district)
                 .group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).all())

    return {
        "scope": ctx.scope, "district": df or "All districts",
        "kpis": kpis, "stream": stream, "alerts": alerts,
        "offenders": offenders, "predictions": predictions,
        "district_breakdown": [{"label": r[0], "value": r[1]} for r in dist_rows],
    }
