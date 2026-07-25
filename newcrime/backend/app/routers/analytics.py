"""Crime pattern & trend analytics + dashboard KPIs."""
from collections import Counter
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _cases_all():
    from ..catalyst_store import get_store
    return get_store().query("SELECT * FROM cases")


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        cases = _cases_all()
        total = len(cases)
        open_cases = sum(1 for c in cases if c.get("status") in ("Open", "Under Investigation"))
        solved = sum(1 for c in cases if c.get("status") in ("Chargesheeted", "Closed"))
        loss = sum(float(c.get("loss_amount", 0)) for c in cases)
        accused = len(store.query("SELECT * FROM accused"))
        profiles = store.query("SELECT * FROM behavior_profiles")
        high_risk = sum(1 for p in profiles if p.get("risk_band") in ("High", "Critical"))
        alerts = len(store.query("SELECT * FROM alerts WHERE resolved = false"))
        return {"total_cases": total, "open_cases": open_cases, "solved_cases": solved,
                "clearance_rate": round(solved / total * 100, 1) if total else 0,
                "total_accused": accused, "high_risk_offenders": high_risk,
                "total_loss": loss, "active_alerts": alerts}

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
    if settings.use_catalyst:
        counts = Counter(c.get("crime_type") for c in _cases_all())
        return sorted([{"label": k, "value": v} for k, v in counts.items()],
                      key=lambda x: -x["value"])

    rows = (db.query(m.Case.crime_type, func.count(m.Case.id))
            .group_by(m.Case.crime_type).order_by(func.count(m.Case.id).desc()).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/by-head")
def by_head(db: Session = Depends(get_db)):
    if settings.use_catalyst:
        counts = Counter(c.get("crime_head") for c in _cases_all())
        return sorted([{"label": k, "value": v} for k, v in counts.items()],
                      key=lambda x: -x["value"])

    rows = (db.query(m.Case.crime_head, func.count(m.Case.id))
            .group_by(m.Case.crime_head).order_by(func.count(m.Case.id).desc()).all())
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/trend")
def trend(db: Session = Depends(get_db), crime_type: str | None = None):
    if settings.use_catalyst:
        cases = _cases_all()
        if crime_type:
            cases = [c for c in cases if c.get("crime_type") == crime_type]
        monthly: dict[str, int] = {}
        for c in cases:
            d = c.get("occurrence_date") or ""
            ym = d[:7] if len(d) >= 7 else None
            if ym:
                monthly[ym] = monthly.get(ym, 0) + 1
        return [{"label": k, "value": v} for k, v in sorted(monthly.items())]

    q = db.query(func.strftime("%Y-%m", m.Case.occurrence_date), func.count(m.Case.id))
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(func.strftime("%Y-%m", m.Case.occurrence_date)) \
            .order_by(func.strftime("%Y-%m", m.Case.occurrence_date)).all()
    return [{"label": r[0], "value": r[1]} for r in rows if r[0]]


@router.get("/hotspots")
def hotspots(db: Session = Depends(get_db), crime_type: str | None = None):
    if settings.use_catalyst:
        cases = _cases_all()
        if crime_type:
            cases = [c for c in cases if c.get("crime_type") == crime_type]
        counts = Counter(c.get("district") for c in cases)
        return sorted([{"label": k, "value": v} for k, v in counts.items()],
                      key=lambda x: -x["value"])

    q = db.query(m.Case.district, func.count(m.Case.id))
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).all()
    return [{"label": r[0], "value": r[1]} for r in rows]


@router.get("/geo")
def geo_points(db: Session = Depends(get_db), crime_type: str | None = None, limit: int = 400):
    if settings.use_catalyst:
        cases = _cases_all()
        if crime_type:
            cases = [c for c in cases if c.get("crime_type") == crime_type]
        return [{"lat": c.get("latitude"), "lon": c.get("longitude"),
                 "crime_type": c.get("crime_type"), "district": c.get("district"),
                 "severity": c.get("severity"), "fir": c.get("fir_number")}
                for c in cases[:limit] if c.get("latitude") and c.get("longitude")]

    q = db.query(m.Case)
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.limit(limit).all()
    return [{"lat": c.latitude, "lon": c.longitude, "crime_type": c.crime_type,
             "district": c.district, "severity": c.severity, "fir": c.fir_number}
            for c in rows if c.latitude and c.longitude]


@router.get("/district-map")
def district_map(request: Request, db: Session = Depends(get_db), crime_type: str | None = None):
    ctx = get_ctx(request)
    df = ctx.district_filter()

    if settings.use_catalyst:
        cases = _cases_all()
        if crime_type:
            cases = [c for c in cases if c.get("crime_type") == crime_type]
        by_dist: dict[str, list] = {}
        for c in cases:
            d = c.get("district") or "Unknown"
            by_dist.setdefault(d, []).append(c)
        out = []
        for dist, dist_cases in by_dist.items():
            count = len(dist_cases)
            lats = [float(c.get("latitude", 0)) for c in dist_cases if c.get("latitude")]
            lons = [float(c.get("longitude", 0)) for c in dist_cases if c.get("longitude")]
            lat = sum(lats) / len(lats) if lats else 0
            lon = sum(lons) / len(lons) if lons else 0
            loss = sum(float(c.get("loss_amount", 0)) for c in dist_cases)
            crime_counts = Counter(c.get("crime_type") for c in dist_cases)
            top_crime = crime_counts.most_common(1)[0][0] if crime_counts else None
            out.append({"district": dist, "count": count, "lat": lat, "lon": lon,
                        "loss": loss, "top_crime": top_crime,
                        "in_scope": (df is None or (dist in df if isinstance(df, list) else dist == df))})
        return {"scope_district": df, "districts": out}

    q = db.query(
        m.Case.district, func.count(m.Case.id), func.avg(m.Case.latitude),
        func.avg(m.Case.longitude), func.sum(m.Case.loss_amount),
    )
    if crime_type:
        q = q.filter(m.Case.crime_type == crime_type)
    rows = q.group_by(m.Case.district).all()
    out = []
    for dist, count, lat, lon, loss in rows:
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
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dows = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    if settings.use_catalyst:
        cases = _cases_all()
        by_month: dict[int, int] = {}
        by_dow: dict[int, int] = {}
        for c in cases:
            d = c.get("occurrence_date")
            if not d:
                continue
            try:
                dt = datetime.fromisoformat(str(d)[:10])
                m_idx = dt.month
                by_month[m_idx] = by_month.get(m_idx, 0) + 1
                by_dow[dt.weekday()] = by_dow.get(dt.weekday(), 0) + 1
            except (ValueError, TypeError):
                pass
        py_dow_to_sun = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
        return {
            "by_month": [{"label": months[m_idx - 1], "value": by_month.get(m_idx, 0)}
                         for m_idx in range(1, 13)],
            "by_weekday": [{"label": dows[d], "value": sum(v for k, v in by_dow.items()
                            if py_dow_to_sun.get(k) == d)} for d in range(7)],
        }

    by_month = (db.query(func.strftime("%m", m.Case.occurrence_date), func.count(m.Case.id))
                .group_by(func.strftime("%m", m.Case.occurrence_date)).all())
    by_dow = (db.query(func.strftime("%w", m.Case.occurrence_date), func.count(m.Case.id))
              .group_by(func.strftime("%w", m.Case.occurrence_date)).all())
    return {
        "by_month": [{"label": months[int(r[0]) - 1], "value": r[1]} for r in by_month if r[0]],
        "by_weekday": [{"label": dows[int(r[0])], "value": r[1]} for r in by_dow if r[0] is not None],
    }


@router.get("/patterns")
def patterns(db: Session = Depends(get_db)):
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        rows = get_store().query("SELECT * FROM crime_patterns ORDER BY case_count DESC")
        return [{"id": p.get("ROWID"), "name": p.get("pattern_name"),
                 "crime_type": p.get("crime_type"), "district": p.get("district"),
                 "temporal": p.get("temporal_signature"), "mo_tags": p.get("modus_operandi_tags"),
                 "case_count": p.get("case_count"), "description": p.get("description")}
                for p in rows]

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
    if settings.use_catalyst:
        return _hotspot_dashboard_catalyst(crime_type, status, station,
                                           date_from, date_to, district)

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
            "loss": loss or 0, "top_crime": top[0] if top else None,
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
            "district": district, "total": dq.count(),
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
        "total_crimes": total, "state_view": state_view, "crime_trend": trend,
        "district_detail": district_detail,
        "filter_options": {"crime_types": crime_types, "statuses": statuses, "stations": stations},
    }


def _hotspot_dashboard_catalyst(crime_type, status, station, date_from, date_to, district):
    cases = _cases_all()
    if crime_type:
        cases = [c for c in cases if c.get("crime_type") == crime_type]
    if status:
        cases = [c for c in cases if c.get("status") == status]
    if station:
        cases = [c for c in cases if c.get("station") == station]
    if date_from:
        cases = [c for c in cases if (c.get("occurrence_date") or "") >= date_from]
    if date_to:
        cases = [c for c in cases if (c.get("occurrence_date") or "") <= date_to]

    total = len(cases)
    by_dist: dict[str, list] = {}
    for c in cases:
        by_dist.setdefault(c.get("district", "Unknown"), []).append(c)

    state_view = []
    for dist, dc in by_dist.items():
        lats = [float(c.get("latitude", 0)) for c in dc if c.get("latitude")]
        lons = [float(c.get("longitude", 0)) for c in dc if c.get("longitude")]
        crime_counts = Counter(c.get("crime_type") for c in dc)
        state_view.append({
            "district": dist, "count": len(dc),
            "lat": sum(lats) / len(lats) if lats else 0,
            "lon": sum(lons) / len(lons) if lons else 0,
            "loss": sum(float(c.get("loss_amount", 0)) for c in dc),
            "top_crime": crime_counts.most_common(1)[0][0] if crime_counts else None,
        })

    monthly: dict[str, int] = {}
    for c in cases:
        ym = (c.get("occurrence_date") or "")[:7]
        if ym:
            monthly[ym] = monthly.get(ym, 0) + 1
    trend = [{"month": k, "count": v} for k, v in sorted(monthly.items())]

    district_detail = None
    if district:
        dc = by_dist.get(district, [])
        by_st = Counter(c.get("station") or "Unknown" for c in dc)
        by_cr = Counter(c.get("crime_type") for c in dc)
        mo: dict[str, int] = {}
        for c in dc:
            ym = (c.get("occurrence_date") or "")[:7]
            if ym:
                mo[ym] = mo.get(ym, 0) + 1
        by_sev = Counter(c.get("severity") or "Unknown" for c in dc)
        district_detail = {
            "district": district, "total": len(dc),
            "by_station": [{"station": k, "count": v} for k, v in by_st.most_common()],
            "by_crime": [{"crime_type": k, "count": v} for k, v in by_cr.most_common()],
            "monthly_trend": [{"month": k, "count": v} for k, v in sorted(mo.items())],
            "by_severity": [{"severity": k, "count": v} for k, v in by_sev.items()],
            "ward_data_available": False,
        }

    all_types = sorted({c.get("crime_type") for c in _cases_all() if c.get("crime_type")})
    all_statuses = sorted({c.get("status") for c in _cases_all() if c.get("status")})
    all_stations = sorted({c.get("station") for c in _cases_all() if c.get("station")})

    return {
        "total_crimes": total, "state_view": state_view, "crime_trend": trend,
        "district_detail": district_detail,
        "filter_options": {"crime_types": all_types, "statuses": all_statuses,
                           "stations": all_stations},
    }


@router.get("/crime-category/{crime_type}")
def crime_category_analytics(crime_type: str, db: Session = Depends(get_db)):
    if settings.use_catalyst:
        return _crime_category_catalyst(crime_type)

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
        alinks = db.query(m.CaseAccused).filter(m.CaseAccused.case_id.in_(case_ids)).all()
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
        "crime_type": crime_type, "total": total,
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
            "total_loss": total_loss, "avg_loss": round(avg_loss, 2),
            "financial_count": financial_count,
        },
    }


def _crime_category_catalyst(crime_type: str):
    from ..catalyst_store import get_store
    store = get_store()
    cases = [c for c in _cases_all() if c.get("crime_type") == crime_type]
    total = len(cases)
    if total == 0:
        return {"crime_type": crime_type, "total": 0, "demographic": {}, "geographic": {},
                "temporal": {}, "behavioural": {}, "summary": {}}

    case_ids = {c.get("ROWID") for c in cases}

    by_district = Counter(c.get("district") or "Unknown" for c in cases)
    by_station = Counter(c.get("station") or "Unknown" for c in cases).most_common(15)
    by_severity = Counter(c.get("severity") or "Unknown" for c in cases)
    by_status = Counter(c.get("status") or "Unknown" for c in cases)

    months_list = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    dows_list = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    monthly: dict[str, int] = {}
    by_month_idx: dict[int, int] = {}
    by_dow: dict[int, int] = {}
    for c in cases:
        d = c.get("occurrence_date")
        if not d:
            continue
        ym = str(d)[:7]
        if ym:
            monthly[ym] = monthly.get(ym, 0) + 1
        try:
            dt = datetime.fromisoformat(str(d)[:10])
            by_month_idx[dt.month] = by_month_idx.get(dt.month, 0) + 1
            by_dow[dt.weekday()] = by_dow.get(dt.weekday(), 0) + 1
        except (ValueError, TypeError):
            pass

    vlinks = store.query("SELECT * FROM case_victim")
    vids = {l.get("victim_id") for l in vlinks if l.get("case_id") in case_ids}
    victims = [v for v in store.query("SELECT * FROM victims") if v.get("ROWID") in vids] if vids else []
    victim_ages = [int(v.get("age", 0)) for v in victims if v.get("age") and int(v.get("age", 0)) > 0]
    victim_genders = [v.get("gender") for v in victims if v.get("gender")]

    age_bands = {"0-17": 0, "18-30": 0, "31-45": 0, "46-60": 0, "60+": 0}
    for a in victim_ages:
        if a <= 17: age_bands["0-17"] += 1
        elif a <= 30: age_bands["18-30"] += 1
        elif a <= 45: age_bands["31-45"] += 1
        elif a <= 60: age_bands["46-60"] += 1
        else: age_bands["60+"] += 1
    gender_counts = Counter(victim_genders)

    alinks = store.query("SELECT * FROM case_accused")
    accused_ids = {l.get("accused_id") for l in alinks if l.get("case_id") in case_ids}
    all_accused = store.query("SELECT * FROM accused")
    accused_statuses = Counter(
        (a.get("status") or "Unknown") for a in all_accused if a.get("ROWID") in accused_ids)

    mo_keywords: dict[str, int] = {}
    for c in cases:
        mo = c.get("modus_operandi") or ""
        for word in mo.lower().split():
            w = word.strip(".,;:!?\"'()[]")
            if len(w) > 3:
                mo_keywords[w] = mo_keywords.get(w, 0) + 1
    top_mo = sorted(mo_keywords.items(), key=lambda x: -x[1])[:15]

    total_loss = sum(float(c.get("loss_amount", 0)) for c in cases)
    avg_loss = total_loss / total if total else 0
    financial_count = sum(1 for c in cases if c.get("is_financial"))

    py_dow_to_sun = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}

    return {
        "crime_type": crime_type, "total": total,
        "demographic": {
            "victim_age_bands": [{"label": k, "value": v} for k, v in age_bands.items()],
            "victim_gender": [{"label": k, "value": v} for k, v in gender_counts.items()],
            "total_victims": len(victim_ages) + len(victim_genders),
        },
        "geographic": {
            "by_district": [{"label": k, "value": v} for k, v in by_district.most_common()],
            "by_station": [{"label": k, "value": v} for k, v in by_station],
        },
        "temporal": {
            "monthly_trend": [{"label": k, "value": v} for k, v in sorted(monthly.items())],
            "by_month": [{"label": months_list[m_i - 1], "value": by_month_idx.get(m_i, 0)}
                         for m_i in range(1, 13)],
            "by_weekday": [{"label": dows_list[d], "value": sum(v for k, v in by_dow.items()
                            if py_dow_to_sun.get(k) == d)} for d in range(7)],
        },
        "behavioural": {
            "accused_status": [{"label": k, "value": v} for k, v in accused_statuses.items()],
            "modus_operandi_keywords": [{"label": w, "value": c} for w, c in top_mo],
        },
        "summary": {
            "by_severity": [{"label": k, "value": v} for k, v in by_severity.items()],
            "by_status": [{"label": k, "value": v} for k, v in by_status.items()],
            "total_loss": total_loss, "avg_loss": round(avg_loss, 2),
            "financial_count": financial_count,
        },
    }
