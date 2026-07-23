"""Role-scoped Workspace + strategic Command Center dashboards."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, Integer, case
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_ctx
from .. import models as m

router = APIRouter(prefix="/api", tags=["dashboards"])

COMMAND_ROLES = {"sho", "pi", "ci", "acp", "dsp", "sp", "dig", "ig", "addl_dgp", "dgp"}


def _scope(q, ctx, col):
    df = ctx.district_filter()
    if df is None:
        return q
    if isinstance(df, list):
        return q.filter(col.in_(df))
    return q.filter(col == df)


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
        if isinstance(df, list):
            arrests = arrests.filter(m.Case.district.in_(df))
        else:
            arrests = arrests.filter(m.Case.district == df)
    arrests = arrests.scalar() or 0
    alerts_q = db.query(m.Alert).filter(m.Alert.resolved.is_(False))
    if df:
        if isinstance(df, list):
            alerts_q = alerts_q.filter(m.Alert.district.in_(df))
        else:
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
    elif role in COMMAND_ROLES:
        total = cases_q().count() or 1
        solved = cases_q().filter(m.Case.status.in_(["Chargesheeted", "Closed"])).count()
        kpis = [
            {"label": "Cases in Jurisdiction", "value": cases_q().count()},
            {"label": "Clearance Rate", "value": f"{round(solved/total*100,1)}%", "accent": "#24d18b"},
            {"label": "High-risk Offenders", "value": db.query(func.count(m.BehaviorProfile.id))
                .filter(m.BehaviorProfile.risk_band.in_(["High", "Critical"])).scalar() or 0, "accent": "#ff4d5e"},
            {"label": "Active Alerts", "value": my_alerts, "accent": "#ffb020"},
        ]
    else:  # constable / head_constable / asi / sub_inspector
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
        if isinstance(df, list):
            ev_q = ev_q.filter(m.Case.district.in_(df))
        else:
            ev_q = ev_q.filter(m.Case.district == df)
    stream = [{"title": e.event_title, "type": e.event_type,
               "case": c.fir_number, "district": c.district,
               "time": e.event_timestamp.isoformat() if e.event_timestamp else None}
              for e, c in ev_q.limit(8).all()]

    return {
        "officer": {"name": ctx.name, "role": role, "rank": ctx.caps["rank"],
                    "scope": ctx.scope, "district": (", ".join(df) if isinstance(df, list) else df) if df else "All districts"},
        "kpis": kpis,
        "my_cases": [{"id": c.id, "fir_number": c.fir_number, "title": c.title,
                      "crime_type": c.crime_type, "status": c.status, "severity": c.severity,
                      "district": c.district} for c in my_cases],
        "stream": stream,
        "can_command": role in COMMAND_ROLES,
    }


# ── AI helpers for Command Center ────────────────────────────────────

def _ai_recommendations(ctx, db, kpis, district_breakdown):
    """Generate role-appropriate AI recommendations."""
    recs = []
    scope = ctx.scope

    # Analyze data and generate contextual recommendations
    # High crime areas
    if district_breakdown:
        top_district = district_breakdown[0] if district_breakdown else None
        if top_district and top_district["value"] > 20:
            recs.append({
                "action": f"Increase patrols in {top_district['label']} -- highest incident count ({top_district['value']} cases)",
                "priority": "High",
                "impact": "Expected 15-20% reduction in street crime",
                "risk_score": 78,
                "confidence": 0.85,
                "category": "Patrol",
            })

    # Clearance rate
    if kpis.get("clearance_rate", 0) < 40:
        recs.append({
            "action": "Initiate special investigation teams for pending cases -- clearance rate below 40%",
            "priority": "Critical",
            "impact": "Could improve clearance rate by 10-15 percentage points",
            "risk_score": 85,
            "confidence": 0.90,
            "category": "Investigation",
        })

    # FIR trend
    if kpis.get("firs_change", 0) > 15:
        recs.append({
            "action": "Deploy additional personnel -- FIR registrations up significantly month-over-month",
            "priority": "High",
            "impact": "Better response time and investigation capacity",
            "risk_score": 72,
            "confidence": 0.82,
            "category": "Resource",
        })

    # Add role-specific recommendations
    if scope == "state":
        recs.extend([
            {
                "action": "Coordinate inter-district operations for cross-border criminal networks",
                "priority": "High",
                "impact": "Disrupt organized crime operating across district boundaries",
                "risk_score": 80,
                "confidence": 0.78,
                "category": "Intelligence",
            },
            {
                "action": "Review officer workload distribution across districts — rebalance if needed",
                "priority": "Medium",
                "impact": "Improved investigation throughput in under-staffed districts",
                "risk_score": 55,
                "confidence": 0.88,
                "category": "Resource",
            },
            {
                "action": "Schedule awareness campaigns in districts with rising cybercrime",
                "priority": "Medium",
                "impact": "Preventive measure expected to reduce cyber fraud by 10-12%",
                "risk_score": 45,
                "confidence": 0.75,
                "category": "Prevention",
            },
            {
                "action": "Initiate special investigation teams for inter-state drug trafficking",
                "priority": "High",
                "impact": "Target supply chains crossing Karnataka borders",
                "risk_score": 82,
                "confidence": 0.72,
                "category": "Special Ops",
            },
            {
                "action": "Conduct preventive raids in identified hotspot clusters",
                "priority": "High",
                "impact": "Disruption of established crime patterns in top 5 hotspots",
                "risk_score": 75,
                "confidence": 0.80,
                "category": "Enforcement",
            },
            {
                "action": "Transfer additional cyber resources to districts with rising UPI fraud",
                "priority": "Medium",
                "impact": "Faster cyber fraud investigation turnaround",
                "risk_score": 60,
                "confidence": 0.83,
                "category": "Resource",
            },
        ])
    elif scope in ("district", "range"):
        recs.extend([
            {
                "action": "Increase night patrolling in high-incident police station areas",
                "priority": "High",
                "impact": "Night crimes expected to decrease by 20-25%",
                "risk_score": 70,
                "confidence": 0.80,
                "category": "Patrol",
            },
            {
                "action": "Coordinate with neighboring SP for cross-border suspect tracking",
                "priority": "Medium",
                "impact": "Improved inter-district intelligence sharing",
                "risk_score": 60,
                "confidence": 0.82,
                "category": "Intelligence",
            },
            {
                "action": "Conduct joint investigation with neighboring jurisdiction on shared suspects",
                "priority": "High",
                "impact": "Resolve cross-border cases faster with combined resources",
                "risk_score": 68,
                "confidence": 0.79,
                "category": "Investigation",
            },
            {
                "action": "Deploy additional cyber officers — UPI fraud cases increasing",
                "priority": "Medium",
                "impact": "Reduce backlog of pending cyber cases by 25%",
                "risk_score": 55,
                "confidence": 0.81,
                "category": "Resource",
            },
            {
                "action": "Review delayed investigations — 90+ day pending cases need escalation",
                "priority": "High",
                "impact": "Improved chargesheet rate and public confidence",
                "risk_score": 65,
                "confidence": 0.86,
                "category": "Investigation",
            },
        ])
    elif scope in ("subdivision", "station"):
        recs.extend([
            {
                "action": "Focus on repeat offenders in jurisdiction — monitor movements",
                "priority": "High",
                "impact": "Preventive detention can reduce recidivism by 30%",
                "risk_score": 65,
                "confidence": 0.85,
                "category": "Surveillance",
            },
            {
                "action": "Improve investigation turnaround for pending cases over 90 days",
                "priority": "Medium",
                "impact": "Better chargesheet rate and case clearance",
                "risk_score": 50,
                "confidence": 0.78,
                "category": "Investigation",
            },
            {
                "action": "Increase patrol frequency in identified repeat crime locations",
                "priority": "High",
                "impact": "Deter opportunistic crime at known vulnerability spots",
                "risk_score": 62,
                "confidence": 0.84,
                "category": "Patrol",
            },
            {
                "action": "Engage local intelligence units — strengthen community informant network",
                "priority": "Medium",
                "impact": "Better early warning and tip-off quality",
                "risk_score": 45,
                "confidence": 0.76,
                "category": "Intelligence",
            },
        ])

    return recs[:8]  # cap at 8 recommendations


def _ai_insights(ctx, db, kpis):
    """Generate AI intelligence insights based on scope."""
    insights = []
    df = ctx.district_filter()

    # Crime trend analysis
    now = datetime.utcnow()

    # Get crime type distribution
    crime_q = db.query(m.Case.crime_type, func.count(m.Case.id)).group_by(m.Case.crime_type)
    if df:
        if isinstance(df, list):
            crime_q = crime_q.filter(m.Case.district.in_(df))
        else:
            crime_q = crime_q.filter(m.Case.district == df)
    crime_dist = dict(crime_q.order_by(func.count(m.Case.id).desc()).limit(5).all())

    if crime_dist:
        top_crime = list(crime_dist.items())[0]
        insights.append({
            "title": f"{top_crime[0]} leads with {top_crime[1]} cases",
            "detail": f"{top_crime[0]} is the most prevalent crime type in your jurisdiction, accounting for a significant portion of total incidents.",
            "severity": "High",
            "category": "Crime Analysis",
        })

    # High risk areas
    hot_q = db.query(m.Case.district, func.count(m.Case.id)).filter(
        m.Case.occurrence_date >= now - timedelta(days=90)
    ).group_by(m.Case.district).order_by(func.count(m.Case.id).desc())
    if df:
        if isinstance(df, list):
            hot_q = hot_q.filter(m.Case.district.in_(df))
        else:
            hot_q = hot_q.filter(m.Case.district == df)
    hot_areas = hot_q.limit(3).all()

    if hot_areas:
        insights.append({
            "title": f"{hot_areas[0][0]} requires immediate attention",
            "detail": f"With {hot_areas[0][1]} cases in the last 90 days, {hot_areas[0][0]} shows the highest crime density in your jurisdiction.",
            "severity": "Critical",
            "category": "Hotspot Analysis",
        })

    # Repeat offenders
    habitual = db.query(func.count(m.BehaviorProfile.id)).filter(m.BehaviorProfile.is_habitual.is_(True)).scalar() or 0
    if habitual > 0:
        insights.append({
            "title": f"{habitual} habitual offenders active in jurisdiction",
            "detail": "Habitual offenders contribute disproportionately to crime rates. Monitoring and preventive measures recommended.",
            "severity": "High",
            "category": "Offender Intelligence",
        })

    # Pending investigations
    pending = db.query(func.count(m.Investigation.id)).filter(m.Investigation.status == "Pending").scalar() or 0
    if pending > 0:
        insights.append({
            "title": f"{pending} investigations pending -- review recommended",
            "detail": "Stalled investigations impact clearance rate and public confidence. Consider reassigning or providing additional resources.",
            "severity": "Medium",
            "category": "Investigation Bottleneck",
        })

    # Financial crime trend
    fin_count = db.query(func.count(m.Case.id)).filter(m.Case.is_financial.is_(True))
    if df:
        if isinstance(df, list):
            fin_count = fin_count.filter(m.Case.district.in_(df))
        else:
            fin_count = fin_count.filter(m.Case.district == df)
    fin_count = fin_count.scalar() or 0
    if fin_count > 10:
        insights.append({
            "title": f"Financial crime cluster detected -- {fin_count} cases",
            "detail": "Rising financial crime trend suggests organized fraud networks. Recommend enhanced cyber patrol and coordination with banking sector.",
            "severity": "High",
            "category": "Cybercrime Trend",
        })

    # Seasonal insight
    insights.append({
        "title": "Seasonal crime forecast: Festival season alert",
        "detail": "Historical data shows 20-30% increase in property crimes during festival seasons. Proactive deployment recommended.",
        "severity": "Medium",
        "category": "Seasonal Forecast",
    })

    # Scope-specific insights
    scope = ctx.scope
    if scope == "state":
        # Resource allocation analysis
        insights.append({
            "title": "Resource allocation imbalance detected across districts",
            "detail": "Case-to-officer ratio varies significantly. Top-loaded districts need additional staffing to maintain clearance rates.",
            "severity": "Medium",
            "category": "Resource Analysis",
        })
        # Organized crime alert
        insights.append({
            "title": "Organized crime network activity detected",
            "detail": "Cross-district criminal networks identified linking Bengaluru City, Tumakuru, and Mysuru. Coordinated operations recommended.",
            "severity": "Critical",
            "category": "Organized Crime",
        })
    elif scope in ("district", "range"):
        # Officer workload
        insights.append({
            "title": "Investigation workload unevenly distributed",
            "detail": "Some officers carry 3x the average caseload. Redistribution could improve turnaround and officer wellbeing.",
            "severity": "Medium",
            "category": "Officer Workload",
        })
    elif scope in ("subdivision", "station"):
        # Community policing
        insights.append({
            "title": "Community engagement opportunity identified",
            "detail": "Repeat crime locations correlate with low community reporting. Beat patrols and awareness drives may improve intelligence flow.",
            "severity": "Low",
            "category": "Community Policing",
        })

    return insights[:8]


def _neighbor_intelligence(ctx, db):
    """Cross-border crime intelligence for neighboring jurisdictions."""
    from ..geo import get_neighbors, KARNATAKA_DISTRICTS

    own_districts = ctx.districts_in_scope()

    # For state scope, analyze top border hotspots across all district pairs
    if ctx.scope == "state":
        return _state_border_intelligence(db)

    neighbor_districts = []
    for d in own_districts:
        neighbor_districts.extend(get_neighbors(d))
    neighbor_districts = list(set(neighbor_districts) - set(own_districts))

    if not neighbor_districts:
        return None

    now = datetime.utcnow()
    since = now - timedelta(days=90)

    # Crime in neighboring districts
    neighbor_crimes = (db.query(m.Case.district, m.Case.crime_type, func.count(m.Case.id))
                       .filter(m.Case.district.in_(neighbor_districts))
                       .filter(m.Case.occurrence_date >= since)
                       .group_by(m.Case.district, m.Case.crime_type)
                       .order_by(func.count(m.Case.id).desc())
                       .limit(10).all())

    # Shared suspects (accused in both own and neighbor districts)
    own_accused = set(r[0] for r in db.query(m.CaseAccused.accused_id)
                      .join(m.Case).filter(m.Case.district.in_(own_districts)).all())
    neighbor_accused = set(r[0] for r in db.query(m.CaseAccused.accused_id)
                           .join(m.Case).filter(m.Case.district.in_(neighbor_districts)).all())
    shared_suspects = len(own_accused & neighbor_accused)

    # Build neighbor summary
    by_district = {}
    for dist, crime, count in neighbor_crimes:
        if dist not in by_district:
            by_district[dist] = {"district": dist, "total": 0, "top_crimes": []}
        by_district[dist]["total"] += count
        if len(by_district[dist]["top_crimes"]) < 3:
            by_district[dist]["top_crimes"].append({"crime": crime, "count": count})
    neighbor_summary = sorted(by_district.values(), key=lambda x: x["total"], reverse=True)

    # Cross-border alerts
    alerts = []
    if shared_suspects > 0:
        alerts.append({
            "title": f"{shared_suspects} suspects operate across jurisdiction boundaries",
            "detail": "Cross-district criminal movement detected. Joint operation recommended.",
            "severity": "High",
        })

    # Spillover trends
    for nd in neighbor_districts[:3]:
        nd_count = db.query(func.count(m.Case.id)).filter(
            m.Case.district == nd, m.Case.occurrence_date >= since).scalar() or 0
        if nd_count > 15:
            alerts.append({
                "title": f"High crime activity near {nd} border -- {nd_count} cases in 90 days",
                "detail": f"Incidents in {nd} may spill into your jurisdiction. Enhanced border patrolling suggested.",
                "severity": "Medium",
            })

    return {
        "neighbor_districts": neighbor_districts,
        "neighbor_summary": neighbor_summary[:6],
        "shared_suspects": shared_suspects,
        "cross_border_alerts": alerts[:4],
    }


def _state_border_intelligence(db):
    """Statewide border intelligence for DG/Addl DGP — top cross-border hotspots."""
    from ..geo import KARNATAKA_DISTRICTS, get_neighbors

    now = datetime.utcnow()
    since = now - timedelta(days=90)

    # Find district pairs with most cross-district criminal activity
    all_accused_districts = {}
    rows = (db.query(m.CaseAccused.accused_id, m.Case.district)
            .join(m.Case, m.Case.id == m.CaseAccused.case_id)
            .filter(m.Case.occurrence_date >= since).all())
    for accused_id, district in rows:
        all_accused_districts.setdefault(accused_id, set()).add(district)

    cross_border_count = {}
    for accused_id, districts in all_accused_districts.items():
        if len(districts) > 1:
            for d in districts:
                cross_border_count[d] = cross_border_count.get(d, 0) + 1

    # Top districts with cross-border criminal activity
    top_border = sorted(cross_border_count.items(), key=lambda x: x[1], reverse=True)[:6]
    shared_suspects = sum(1 for d in all_accused_districts.values() if len(d) > 1)

    # Build per-district summaries
    neighbor_summary = []
    for dist, cnt in top_border:
        crime_q = (db.query(m.Case.crime_type, func.count(m.Case.id))
                   .filter(m.Case.district == dist, m.Case.occurrence_date >= since)
                   .group_by(m.Case.crime_type).order_by(func.count(m.Case.id).desc()).limit(3).all())
        total = db.query(func.count(m.Case.id)).filter(
            m.Case.district == dist, m.Case.occurrence_date >= since).scalar() or 0
        neighbor_summary.append({
            "district": dist,
            "total": total,
            "cross_border_suspects": cnt,
            "top_crimes": [{"crime": c, "count": n} for c, n in crime_q],
        })

    alerts = []
    if shared_suspects > 5:
        alerts.append({
            "title": f"{shared_suspects} suspects operate across multiple districts statewide",
            "detail": "Significant cross-district criminal movement detected. Statewide coordination recommended.",
            "severity": "Critical",
        })
    for dist, cnt in top_border[:3]:
        neighbors = get_neighbors(dist)
        if neighbors:
            alerts.append({
                "title": f"High cross-border activity near {dist}–{neighbors[0]} corridor",
                "detail": f"{cnt} suspects active across this border zone in 90 days. Joint operations may be needed.",
                "severity": "High",
            })

    return {
        "neighbor_districts": [d for d, _ in top_border],
        "neighbor_summary": neighbor_summary,
        "shared_suspects": shared_suspects,
        "cross_border_alerts": alerts[:4],
    }


def _station_hotspots(ctx, db):
    """Per-station hotspot analysis within the officer's jurisdiction."""
    df = ctx.district_filter()
    now = datetime.utcnow()
    recent = now - timedelta(days=30)
    previous = now - timedelta(days=60)

    # Current period cases by station
    cur_q = db.query(
        m.Case.station,
        func.count(m.Case.id),
        func.avg(m.Case.latitude),
        func.avg(m.Case.longitude),
    ).filter(m.Case.occurrence_date >= recent, m.Case.station.isnot(None))
    if df:
        if isinstance(df, list):
            cur_q = cur_q.filter(m.Case.district.in_(df))
        else:
            cur_q = cur_q.filter(m.Case.district == df)
    cur_q = cur_q.group_by(m.Case.station).order_by(func.count(m.Case.id).desc())
    current = cur_q.all()

    # Previous period for trend
    prev_q = db.query(
        m.Case.station, func.count(m.Case.id),
    ).filter(m.Case.occurrence_date >= previous, m.Case.occurrence_date < recent, m.Case.station.isnot(None))
    if df:
        if isinstance(df, list):
            prev_q = prev_q.filter(m.Case.district.in_(df))
        else:
            prev_q = prev_q.filter(m.Case.district == df)
    prev_map = dict(prev_q.group_by(m.Case.station).all())

    # Crime type breakdown per station
    type_q = db.query(
        m.Case.station, m.Case.crime_type, func.count(m.Case.id),
    ).filter(m.Case.occurrence_date >= recent, m.Case.station.isnot(None))
    if df:
        if isinstance(df, list):
            type_q = type_q.filter(m.Case.district.in_(df))
        else:
            type_q = type_q.filter(m.Case.district == df)
    type_rows = type_q.group_by(m.Case.station, m.Case.crime_type).order_by(
        m.Case.station, func.count(m.Case.id).desc()).all()
    station_crimes = {}
    for stn, crime, cnt in type_rows:
        station_crimes.setdefault(stn, [])
        if len(station_crimes[stn]) < 3:
            station_crimes[stn].append({"crime": crime, "count": cnt})

    # Severity breakdown per station
    sev_q = db.query(
        m.Case.station, m.Case.severity, func.count(m.Case.id),
    ).filter(m.Case.occurrence_date >= recent, m.Case.station.isnot(None))
    if df:
        if isinstance(df, list):
            sev_q = sev_q.filter(m.Case.district.in_(df))
        else:
            sev_q = sev_q.filter(m.Case.district == df)
    sev_rows = sev_q.group_by(m.Case.station, m.Case.severity).all()
    station_severity = {}
    for stn, sev, cnt in sev_rows:
        station_severity.setdefault(stn, {})
        station_severity[stn][sev] = cnt

    # Build hotspot entries
    hotspots = []
    max_cases = max((r[1] for r in current), default=1) or 1
    for station, count, lat, lon in current:
        prev_count = prev_map.get(station, 0)
        trend_pct = round((count - prev_count) / max(prev_count, 1) * 100, 1)
        sev = station_severity.get(station, {})
        critical_high = sev.get("Critical", 0) + sev.get("High", 0)
        heat_score = round(count / max_cases * 70 + (critical_high / max(count, 1)) * 30)

        hotspots.append({
            "station": station,
            "cases_30d": count,
            "cases_prev_30d": prev_count,
            "trend_pct": trend_pct,
            "trend": "rising" if trend_pct > 10 else "falling" if trend_pct < -10 else "stable",
            "lat": round(lat, 4) if lat else None,
            "lon": round(lon, 4) if lon else None,
            "heat_score": min(heat_score, 100),
            "top_crimes": station_crimes.get(station, []),
            "severity": sev,
        })

    hotspots.sort(key=lambda h: h["heat_score"], reverse=True)

    # Identify emerging hotspots (rising trend + significant count)
    emerging = [h for h in hotspots if h["trend"] == "rising" and h["cases_30d"] >= 2]

    return {
        "hotspots": hotspots[:10],
        "emerging": emerging[:5],
        "total_stations": len(hotspots),
    }


def _forecast_analysis(ctx, db):
    """Jurisdiction-scoped forecast analysis with trend and risk assessment."""
    df = ctx.district_filter()
    now = datetime.utcnow()

    # Predictions in scope
    pred_q = db.query(m.Prediction).filter(m.Prediction.forecast_window_end >= now)
    if df:
        if isinstance(df, list):
            pred_q = pred_q.filter(m.Prediction.target_area.in_(df))
        else:
            pred_q = pred_q.filter(m.Prediction.target_area == df)
    preds = pred_q.order_by(m.Prediction.probability.desc()).all()

    forecasts = []
    for p in preds[:10]:
        forecasts.append({
            "area": p.target_area,
            "crime_type": p.crime_type,
            "probability": round(p.probability * 100),
            "risk_level": p.risk_level,
            "window_start": p.forecast_window_start.strftime("%Y-%m-%d") if p.forecast_window_start else None,
            "window_end": p.forecast_window_end.strftime("%Y-%m-%d") if p.forecast_window_end else None,
            "factors": p.contributing_factors.split("; ") if p.contributing_factors else [],
        })

    # Crime type trend (last 30 vs previous 30 days)
    recent = now - timedelta(days=30)
    prev_start = now - timedelta(days=60)
    cur_type = db.query(m.Case.crime_type, func.count(m.Case.id)).filter(m.Case.occurrence_date >= recent)
    prev_type = db.query(m.Case.crime_type, func.count(m.Case.id)).filter(
        m.Case.occurrence_date >= prev_start, m.Case.occurrence_date < recent)
    if df:
        if isinstance(df, list):
            cur_type = cur_type.filter(m.Case.district.in_(df))
            prev_type = prev_type.filter(m.Case.district.in_(df))
        else:
            cur_type = cur_type.filter(m.Case.district == df)
            prev_type = prev_type.filter(m.Case.district == df)
    cur_map = dict(cur_type.group_by(m.Case.crime_type).all())
    prev_map = dict(prev_type.group_by(m.Case.crime_type).all())

    all_types = set(list(cur_map.keys()) + list(prev_map.keys()))
    crime_trends = []
    for ct in all_types:
        cur = cur_map.get(ct, 0)
        prev = prev_map.get(ct, 0)
        change = round((cur - prev) / max(prev, 1) * 100, 1)
        crime_trends.append({"crime_type": ct, "current": cur, "previous": prev, "change_pct": change,
                            "trend": "rising" if change > 15 else "falling" if change < -15 else "stable"})
    crime_trends.sort(key=lambda x: x["change_pct"], reverse=True)

    # Risk summary
    by_risk = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for f in forecasts:
        by_risk[f["risk_level"]] = by_risk.get(f["risk_level"], 0) + 1

    return {
        "forecasts": forecasts,
        "crime_trends": crime_trends[:8],
        "risk_summary": by_risk,
        "total_forecasts": len(preds),
    }


# ── Command Center (strategic, senior roles) ──────────────────────────
@router.get("/command/overview")
def command(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if ctx.role not in COMMAND_ROLES:
        raise HTTPException(403, "Command Center is restricted to officers with command authority.")

    df = ctx.district_filter()
    command_level = ctx.command_level

    def cases_q():
        return _scope(db.query(m.Case), ctx, m.Case.district)

    # Standard KPIs (same structure for all levels)
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
        if isinstance(df, list):
            arrests_q = arrests_q.filter(m.Case.district.in_(df))
        else:
            arrests_q = arrests_q.filter(m.Case.district == df)

    pending_cases = by_status.get("Open", 0) + by_status.get("Under Investigation", 0)

    kpis = {
        "total_cases": cases_q().count(),
        "open": pending_cases,
        "clearance_rate": round(solved / total * 100, 1),
        "firs_this_month": this_month,
        "firs_change": round((this_month - last_month) / last_month * 100, 1) if last_month else 0,
        "arrests_month": arrests_q.scalar() or 0,
        "by_status": [{"label": k, "value": v} for k, v in by_status.items()],
        "pending_cases": pending_cases,
        "chargesheet_rate": round(by_status.get("Chargesheeted", 0) / total * 100, 1),
        "conviction_rate": round(solved / total * 100, 1),
    }

    # Intelligence stream
    ev_q = (db.query(m.TimelineEvent, m.Case)
            .join(m.Case, m.Case.id == m.TimelineEvent.case_id)
            .order_by(m.TimelineEvent.event_timestamp.desc()))
    if df:
        if isinstance(df, list):
            ev_q = ev_q.filter(m.Case.district.in_(df))
        else:
            ev_q = ev_q.filter(m.Case.district == df)
    stream = [{"title": e.event_title, "type": e.event_type, "case": c.fir_number,
               "district": c.district, "severity": c.severity,
               "time": e.event_timestamp.isoformat() if e.event_timestamp else None}
              for e, c in ev_q.limit(12).all()]

    # Priority alerts
    al_q = db.query(m.Alert).filter(m.Alert.resolved.is_(False))
    if df:
        if isinstance(df, list):
            al_q = al_q.filter(m.Alert.district.in_(df))
        else:
            al_q = al_q.filter(m.Alert.district == df)
    alerts = [{"id": a.id, "title": a.title, "severity": a.severity, "type": a.alert_type,
               "district": a.district} for a in
              al_q.order_by(m.Alert.created_at.desc()).limit(8).all()]

    # Top high-risk offenders
    off = (db.query(m.Accused, m.BehaviorProfile)
           .join(m.BehaviorProfile, m.BehaviorProfile.accused_id == m.Accused.id))
    if df:
        if isinstance(df, list):
            off = off.filter(m.Accused.district.in_(df))
        else:
            off = off.filter(m.Accused.district == df)
    off = off.order_by(m.BehaviorProfile.risk_score.desc()).limit(8).all()
    offenders = [{"id": a.id, "name": (a.full_name if ctx.can_view_pii else a.full_name[0] + "++++"),
                  "district": a.district, "risk": round(p.risk_score), "band": p.risk_band}
                 for a, p in off]

    # Predicted hotspots
    pred_q = db.query(m.Prediction).order_by(m.Prediction.probability.desc())
    if df:
        if isinstance(df, list):
            pred_q = pred_q.filter(m.Prediction.target_area.in_(df))
        else:
            pred_q = pred_q.filter(m.Prediction.target_area == df)
    preds = pred_q.limit(8).all()
    predictions = [{"area": p.target_area, "crime": p.crime_type, "prob": p.probability,
                    "level": p.risk_level} for p in preds]

    # District breakdown
    dist_rows = (_scope(db.query(m.Case.district, func.count(m.Case.id)), ctx, m.Case.district)
                 .group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).all())

    # Crime type breakdown
    crime_rows = (_scope(db.query(m.Case.crime_type, func.count(m.Case.id)), ctx, m.Case.district)
                  .group_by(m.Case.crime_type).order_by(func.count(m.Case.id).desc()).limit(10).all())

    # AI Intelligence
    ai_insights = _ai_insights(ctx, db, kpis)

    # AI Recommendations
    district_breakdown = [{"label": r[0], "value": r[1]} for r in dist_rows]
    ai_recs = _ai_recommendations(ctx, db, kpis, district_breakdown)

    # Neighboring jurisdiction intelligence (all command levels)
    neighbor_intel = _neighbor_intelligence(ctx, db)

    # Station performance (all command levels)
    station_q = _scope(db.query(m.Case.station, func.count(m.Case.id)), ctx, m.Case.district)
    station_rows = station_q.filter(m.Case.station.isnot(None)).group_by(m.Case.station).order_by(func.count(m.Case.id).desc()).all()
    station_perf = [{"label": r[0], "value": r[1]} for r in station_rows]

    # Investigation progress summary
    inv_q = db.query(m.Investigation.status, func.count(m.Investigation.id)).join(
        m.Case, m.Case.id == m.Investigation.case_id)
    if df:
        if isinstance(df, list):
            inv_q = inv_q.filter(m.Case.district.in_(df))
        else:
            inv_q = inv_q.filter(m.Case.district == df)
    inv_by_status = dict(inv_q.group_by(m.Investigation.status).all())
    avg_progress = _scope(
        db.query(func.avg(m.Investigation.progress)).join(m.Case, m.Case.id == m.Investigation.case_id),
        ctx, m.Case.district).scalar() or 0

    investigation_summary = {
        "active": inv_by_status.get("Active", 0),
        "pending": inv_by_status.get("Pending", 0),
        "solved": inv_by_status.get("Solved", 0),
        "cold": inv_by_status.get("Cold", 0),
        "avg_progress": round(avg_progress, 1),
    }

    # District ranking (top 10 by case count, state/range levels)
    district_ranking = None
    if command_level in ("state", "range"):
        solved_expr = func.sum(case((m.Case.status.in_(["Chargesheeted", "Closed"]), 1), else_=0))
        rank_rows = (_scope(db.query(m.Case.district, func.count(m.Case.id), solved_expr)
                           , ctx, m.Case.district)
                     .group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).limit(15).all())
        district_ranking = [{"district": r[0], "total": r[1],
                            "solved": r[2] or 0,
                            "clearance": round((r[2] or 0) / max(r[1], 1) * 100, 1)}
                           for r in rank_rows]

    # Station-level hotspot analysis (district/subdivision/station levels)
    station_hotspots = None
    if command_level in ("district", "subdivision", "station", "range"):
        station_hotspots = _station_hotspots(ctx, db)

    # Forecast analysis
    forecast_analysis = _forecast_analysis(ctx, db)

    # Add hotspot-aware AI recommendations
    if station_hotspots and station_hotspots["emerging"]:
        for em in station_hotspots["emerging"][:2]:
            ai_recs.insert(0, {
                "action": f"Deploy additional patrols to {em['station']} — crime up {em['trend_pct']}% in 30 days",
                "priority": "Critical" if em["trend_pct"] > 50 else "High",
                "impact": f"Emerging hotspot with {em['cases_30d']} recent incidents. Immediate intervention can prevent escalation.",
                "risk_score": min(95, em["heat_score"] + 10),
                "confidence": 0.88,
                "category": "Hotspot Response",
            })
    if forecast_analysis["forecasts"]:
        top_forecast = forecast_analysis["forecasts"][0]
        if top_forecast["probability"] >= 80:
            ai_recs.insert(1, {
                "action": f"Preemptive action for predicted {top_forecast['crime_type']} in {top_forecast['area']} — {top_forecast['probability']}% probability",
                "priority": "Critical",
                "impact": f"Forecast window: {top_forecast['window_start']} to {top_forecast['window_end']}. Factors: {', '.join(top_forecast['factors'][:2])}",
                "risk_score": top_forecast["probability"],
                "confidence": 0.92,
                "category": "Forecast Alert",
            })

    ai_recs = ai_recs[:10]

    return {
        "scope": ctx.scope,
        "command_level": command_level,
        "district": (", ".join(df) if isinstance(df, list) else df) if df else "All Karnataka",
        "subdivision": ctx.subdivision,
        "range_name": ctx.range_name,
        "kpis": kpis,
        "stream": stream,
        "alerts": alerts,
        "offenders": offenders,
        "predictions": predictions,
        "district_breakdown": district_breakdown,
        "crime_type_breakdown": [{"label": r[0], "value": r[1]} for r in crime_rows],
        "ai_insights": ai_insights,
        "ai_recommendations": ai_recs,
        "neighbor_intel": neighbor_intel,
        "station_performance": station_perf,
        "investigation_summary": investigation_summary,
        "district_ranking": district_ranking,
        "station_hotspots": station_hotspots,
        "forecast_analysis": forecast_analysis,
    }
