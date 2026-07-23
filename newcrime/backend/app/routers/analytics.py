"""Crime pattern & trend analytics + dashboard KPIs."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    total = db.query(func.count(m.Case.id)).scalar() or 0
    open_cases = db.query(func.count(m.Case.id)).filter(
        m.Case.status.in_(["Open", "Under Investigation"])).scalar() or 0
    solved = db.query(func.count(m.Case.id)).filter(
        m.Case.status.in_(["Chargesheeted", "Closed"])).scalar() or 0
    accused = db.query(func.count(m.Accused.id)).scalar() or 0
    high_risk = db.query(func.count(m.BehaviorProfile.id)).filter(
        m.BehaviorProfile.risk_band.in_(["High", "Critical"])).scalar() or 0
    loss = db.query(func.sum(m.Case.loss_amount)).scalar() or 0
    alerts = db.query(func.count(m.Alert.id)).filter(m.Alert.resolved.is_(False)).scalar() or 0
    return {"total_cases": total, "open_cases": open_cases, "solved_cases": solved,
            "clearance_rate": round(solved / total * 100, 1) if total else 0,
            "total_accused": accused, "high_risk_offenders": high_risk,
            "total_loss": loss, "active_alerts": alerts}


@router.get("/by-type")
def by_type(db: Session = Depends(get_db)):
    rows = (db.query(m.Case.crime_type, func.count(m.Case.id))
            .group_by(m.Case.crime_type).order_by(func.count(m.Case.id).desc()).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/by-head")
def by_head(db: Session = Depends(get_db)):
    rows = (db.query(m.Case.crime_head, func.count(m.Case.id))
            .group_by(m.Case.crime_head).order_by(func.count(m.Case.id).desc()).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/trend")
def trend(db: Session = Depends(get_db), crime_type: str | None = None):
    q = db.query(func.strftime("%Y-%m", m.Case.occurrence_date), func.count(m.Case.id))
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(func.strftime("%Y-%m", m.Case.occurrence_date)) \
            .order_by(func.strftime("%Y-%m", m.Case.occurrence_date)).all()
    return [{"label": r[0], "value": r[1]} for r in rows if r[0]]


@router.get("/hotspots")
def hotspots(db: Session = Depends(get_db), crime_type: str | None = None):
    q = db.query(m.Case.district, func.count(m.Case.id))
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).all()
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/geo")
def geo_points(db: Session = Depends(get_db), crime_type: str | None = None, limit: int = 400):
    q = db.query(m.Case)
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.limit(limit).all()
    return [{"lat": c.latitude, "lon": c.longitude, "crime_type": c.crime_type,
             "district": c.district, "severity": c.severity, "fir": c.fir_number}
            for c in rows if c.latitude and c.longitude]


@router.get("/district-map")
def district_map(request: Request, db: Session = Depends(get_db), crime_type: str | None = None):
    """Per-district centroid + incident density for the Karnataka heat map."""
    ctx = get_ctx(request)
    df = ctx.district_filter()
    q = db.query(
        m.Case.district,
        func.count(m.Case.id),
        func.avg(m.Case.latitude),
        func.avg(m.Case.longitude),
        func.sum(m.Case.loss_amount),
    )
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(m.Case.district).all()
    out = []
    for dist, count, lat, lon, loss in rows:
        # top crime for the district
        top = (db.query(m.Case.crime_type, func.count(m.Case.id))
               .filter(m.Case.district == dist)
               .group_by(m.Case.crime_type)
               .order_by(func.count(m.Case.id).desc()).first())
        out.append({"district": dist, "count": count, "lat": lat, "lon": lon,
                    "loss": loss or 0, "top_crime": top[0] if top else None,
                    "in_scope": (df is None or (dist in df if isinstance(df, list) else dist == df))})
    return {"scope_district": df, "districts": out}


@router.get("/temporal")
def temporal(db: Session = Depends(get_db)):
    """Seasonal / weekday signature (by month-of-year and day-of-week)."""
    by_month = (db.query(func.strftime("%m", m.Case.occurrence_date), func.count(m.Case.id))
                .group_by(func.strftime("%m", m.Case.occurrence_date)).all())
    by_dow = (db.query(func.strftime("%w", m.Case.occurrence_date), func.count(m.Case.id))
              .group_by(func.strftime("%w", m.Case.occurrence_date)).all())
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dows = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    return {
        "by_month": [{"label": months[int(r[0]) - 1], "value": r[1]} for r in by_month if r[0]],
        "by_weekday": [{"label": dows[int(r[0])], "value": r[1]} for r in by_dow if r[0] is not None],
    }


@router.get("/patterns")
def patterns(db: Session = Depends(get_db)):
    rows = db.query(m.CrimePattern).order_by(m.CrimePattern.case_count.desc()).all()
    return [{"id": p.id, "name": p.pattern_name, "crime_type": p.crime_type,
             "district": p.district, "temporal": p.temporal_signature,
             "mo_tags": p.modus_operandi_tags, "case_count": p.case_count,
             "description": p.description} for p in rows]


@router.get("/hotspot-dashboard")
def hotspot_dashboard(
    request: Request, db: Session = Depends(get_db),
    crime_type: str = "", status: str = "", station: str = "",
    date_from: str = "", date_to: str = "", district: str = "",
):
    q = db.query(m.Case)
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    if status:
        q = q.filter(m.Case.status == status)
    if station:
        q = q.filter(m.Case.station == station)
    if date_from:
        try:
            q = q.filter(m.Case.occurrence_date >= datetime.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(m.Case.occurrence_date <= datetime.fromisoformat(date_to))
        except ValueError:
            pass

    total = q.count()

    district_agg = (q.with_entities(
        m.Case.district, func.count(m.Case.id), func.avg(m.Case.latitude),
        func.avg(m.Case.longitude), func.sum(m.Case.loss_amount))
        .group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).all())

    state_view = []
    for dist, cnt, lat, lon, loss in district_agg:
        top = (q.with_entities(m.Case.crime_type, func.count(m.Case.id))
               .filter(m.Case.district == dist)
               .group_by(m.Case.crime_type)
               .order_by(func.count(m.Case.id).desc()).first())
        state_view.append({
            "district": dist, "count": cnt,
            "lat": lat or 0, "lon": lon or 0,
            "loss": loss or 0,
            "top_crime": top[0] if top else None,
        })

    trend_rows = (q.with_entities(
        func.strftime("%Y-%m", m.Case.occurrence_date), func.count(m.Case.id))
        .filter(m.Case.occurrence_date.isnot(None))
        .group_by(func.strftime("%Y-%m", m.Case.occurrence_date))
        .order_by(func.strftime("%Y-%m", m.Case.occurrence_date)).all())
    trend = [{"month": r[0], "count": r[1]} for r in trend_rows if r[0]]

    district_detail = None
    if district:
        dq = q.filter(m.Case.district == district)
        by_station = (dq.with_entities(m.Case.station, func.count(m.Case.id))
                      .group_by(m.Case.station)
                      .order_by(func.count(m.Case.id).desc()).all())
        by_crime = (dq.with_entities(m.Case.crime_type, func.count(m.Case.id))
                    .group_by(m.Case.crime_type)
                    .order_by(func.count(m.Case.id).desc()).all())
        monthly = (dq.with_entities(
            func.strftime("%Y-%m", m.Case.occurrence_date), func.count(m.Case.id))
            .filter(m.Case.occurrence_date.isnot(None))
            .group_by(func.strftime("%Y-%m", m.Case.occurrence_date))
            .order_by(func.strftime("%Y-%m", m.Case.occurrence_date)).all())
        severity = (dq.with_entities(m.Case.severity, func.count(m.Case.id))
                    .group_by(m.Case.severity).all())
        district_detail = {
            "district": district,
            "total": dq.count(),
            "by_station": [{"station": r[0] or "Unknown", "count": r[1]} for r in by_station],
            "by_crime": [{"crime_type": r[0], "count": r[1]} for r in by_crime],
            "monthly_trend": [{"month": r[0], "count": r[1]} for r in monthly if r[0]],
            "by_severity": [{"severity": r[0] or "Unknown", "count": r[1]} for r in severity],
            "ward_data_available": False,
        }

    crime_types = [r[0] for r in db.query(m.Case.crime_type).distinct().order_by(m.Case.crime_type).all() if r[0]]
    statuses = [r[0] for r in db.query(m.Case.status).distinct().order_by(m.Case.status).all() if r[0]]
    stations = [r[0] for r in db.query(m.Case.station).distinct().order_by(m.Case.station).all() if r[0]]

    return {
        "total_crimes": total,
        "state_view": state_view,
        "crime_trend": trend,
        "district_detail": district_detail,
        "filter_options": {
            "crime_types": crime_types,
            "statuses": statuses,
            "stations": stations,
        },
    }


@router.get("/crime-category/{crime_type}")
def crime_category_analytics(crime_type: str, db: Session = Depends(get_db)):
    q = db.query(m.Case).filter(m.Case.crime_type == crime_type)
    total = q.count()
    if total == 0:
        return {"crime_type": crime_type, "total": 0, "demographic": {}, "geographic": {},
                "temporal": {}, "behavioural": {}, "summary": {}}

    by_district = (q.with_entities(m.Case.district, func.count(m.Case.id))
                   .group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).all())
    by_station = (q.with_entities(m.Case.station, func.count(m.Case.id))
                  .group_by(m.Case.station).order_by(func.count(m.Case.id).desc()).limit(15).all())
    by_severity = (q.with_entities(m.Case.severity, func.count(m.Case.id))
                   .group_by(m.Case.severity).all())
    by_status = (q.with_entities(m.Case.status, func.count(m.Case.id))
                 .group_by(m.Case.status).all())

    monthly = (q.with_entities(func.strftime("%Y-%m", m.Case.occurrence_date), func.count(m.Case.id))
               .filter(m.Case.occurrence_date.isnot(None))
               .group_by(func.strftime("%Y-%m", m.Case.occurrence_date))
               .order_by(func.strftime("%Y-%m", m.Case.occurrence_date)).all())
    by_month = (q.with_entities(func.strftime("%m", m.Case.occurrence_date), func.count(m.Case.id))
                .filter(m.Case.occurrence_date.isnot(None))
                .group_by(func.strftime("%m", m.Case.occurrence_date)).all())
    by_dow = (q.with_entities(func.strftime("%w", m.Case.occurrence_date), func.count(m.Case.id))
              .filter(m.Case.occurrence_date.isnot(None))
              .group_by(func.strftime("%w", m.Case.occurrence_date)).all())

    case_ids = [c.id for c in q.with_entities(m.Case.id).all()]

    victim_ages = []
    victim_genders = []
    if case_ids:
        vlinks = (db.query(m.CaseVictim.victim_id)
                  .filter(m.CaseVictim.case_id.in_(case_ids)).all())
        vids = list({v[0] for v in vlinks})
        if vids:
            victims = db.query(m.Victim).filter(m.Victim.id.in_(vids)).all()
            for v in victims:
                if v.age and v.age > 0:
                    victim_ages.append(v.age)
                if v.gender:
                    victim_genders.append(v.gender)

    age_bands = {"0-17": 0, "18-30": 0, "31-45": 0, "46-60": 0, "60+": 0}
    for a in victim_ages:
        if a <= 17: age_bands["0-17"] += 1
        elif a <= 30: age_bands["18-30"] += 1
        elif a <= 45: age_bands["31-45"] += 1
        elif a <= 60: age_bands["46-60"] += 1
        else: age_bands["60+"] += 1

    gender_counts: dict[str, int] = {}
    for g in victim_genders:
        gender_counts[g] = gender_counts.get(g, 0) + 1

    accused_statuses: dict[str, int] = {}
    mo_keywords: dict[str, int] = {}
    if case_ids:
        alinks = (db.query(m.CaseAccused).filter(m.CaseAccused.case_id.in_(case_ids))
                  .all())
        for al in alinks:
            acc = al.accused
            st = acc.status or "Unknown"
            accused_statuses[st] = accused_statuses.get(st, 0) + 1

        for c in q.all():
            if c.modus_operandi:
                for word in c.modus_operandi.lower().split():
                    w = word.strip(".,;:!?\"'()[]")
                    if len(w) > 3:
                        mo_keywords[w] = mo_keywords.get(w, 0) + 1

    top_mo = sorted(mo_keywords.items(), key=lambda x: -x[1])[:15]

    total_loss = q.with_entities(func.sum(m.Case.loss_amount)).scalar() or 0
    avg_loss = q.with_entities(func.avg(m.Case.loss_amount)).scalar() or 0
    financial_count = q.filter(m.Case.is_financial.is_(True)).count()

    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dows_list = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    return {
        "crime_type": crime_type,
        "total": total,
        "demographic": {
            "victim_age_bands": [{"label": k, "value": v} for k, v in age_bands.items()],
            "victim_gender": [{"label": k, "value": v} for k, v in gender_counts.items()],
            "total_victims": len(victim_ages) + len([g for g in victim_genders if g]),
        },
        "geographic": {
            "by_district": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_district],
            "by_station": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_station],
        },
        "temporal": {
            "monthly_trend": [{"label": r[0], "value": r[1]} for r in monthly if r[0]],
            "by_month": [{"label": months_list[int(r[0]) - 1], "value": r[1]} for r in by_month if r[0]],
            "by_weekday": [{"label": dows_list[int(r[0])], "value": r[1]} for r in by_dow if r[0] is not None],
        },
        "behavioural": {
            "accused_status": [{"label": k, "value": v} for k, v in accused_statuses.items()],
            "modus_operandi_keywords": [{"label": w, "value": c} for w, c in top_mo],
        },
        "summary": {
            "by_severity": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_severity],
            "by_status": [{"label": r[0] or "Unknown", "value": r[1]} for r in by_status],
            "total_loss": total_loss,
            "avg_loss": round(avg_loss, 2),
            "financial_count": financial_count,
        },
    }
