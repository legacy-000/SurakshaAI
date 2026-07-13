import logging
import sys, os
from flask import Request, jsonify
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, 'common'))

from common.main_handler import SurakshaAIHandler
from common.models.dto import (
    LoginRequestDTO, QueryRequestDTO, UserContextDTO,
    CrimeTrendRequestDTO, HotspotRequestDTO, ForecastRequestDTO
)

logger = logging.getLogger()


def handler(request: Request):
    app = None
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize(req=request)
    except Exception as e:
        logger.error("Failed to initialize Catalyst SDK: %s", e)

    ai_handler = SurakshaAIHandler(app)
    body = request.get_json(force=True, silent=True) or {}
    action = body.get("action", "")
    params = body.get("params", {})
    session = body.get("session", {})
    uc = session.get("user_context", {})

    user_context = UserContextDTO(
        user_id=uc.get("user_id", "convokraft"),
        kgid=uc.get("kgid", ""),
        first_name=uc.get("first_name", ""),
        email=uc.get("email", ""),
        role_id=uc.get("role_id", 1),
        role_name=uc.get("role_name", ""),
        unit_id=uc.get("unit_id"),
        district_id=uc.get("district_id"),
        language_preference=uc.get("language_preference", "en"),
    ) if uc else None

    db_required_actions = {
        "chat_query", "get_crime_stats", "get_trends", "get_hotspots",
        "get_forecast", "get_offender_profile", "get_network",
        "get_dashboard_kpis", "get_alerts", "create_offender_profile",
        "import_table"
    }

    if action in db_required_actions and not ai_handler.is_live:
        return jsonify({"error": "DB_NOT_CONNECTED", "message": "Zoho Catalyst connection required but unavailable."}), 500

    try:
        if action in ("get_crime_stats", "chat_query"):
            message = params.get("message", params.get("query", ""))
            req = QueryRequestDTO(message=message, lang=params.get("lang", "en"))
            result = ai_handler.chat.handle_query(req, user_context)
            if hasattr(result, "content_text") and "DB_NOT_CONNECTED" in result.content_text:
                return jsonify({"error": "DB_NOT_CONNECTED", "message": result.content_text}), 500
            return jsonify({
                "message_id": result.message_id, "message_type": result.message_type,
                "content_text": result.content_text, "content_kannada": result.content_kannada or "",
                "sql_text": result.sql_text, "chart_recommendation": result.chart_recommendation,
                "evidence_refs": [e.model_dump() for e in result.evidence_refs],
                "confidence_class": result.confidence_class,
                "suggested_followups": result.suggested_followups,
                "created_at": result.created_at or datetime.utcnow().isoformat()
            }), 200

        elif action == "login":
            req = LoginRequestDTO(kgid=params.get("kgid", ""), password=params.get("password", ""))
            res = ai_handler.auth.login(req)
            return jsonify(res), 200

        elif action == "get_forecast":
            req = ForecastRequestDTO(
                district_id=params.get("district_id", 1),
                crime_sub_head_id=params.get("crime_sub_head_id", 1),
                forecast_horizon_days=30, training_window_days=365
            )
            categories = params.get("categories")
            districts = params.get("districts")
            results = []
            loop = [{"label": c, "key": "category"} for c in (categories or [params.get("category", "Theft")])] + \
                   [{"label": d, "key": "district"} for d in (districts or [])]
            for item in loop:
                if item["key"] == "district":
                    req.district_id = params.get("district_id", 1)
                    cat = params.get("category", "Theft")
                else:
                    cat = item["label"]
                res = ai_handler.forecaster.forecast(req)
                pts = [{"date": p.date, "predicted": p.predicted, "upper": p.upper, "lower": p.lower,
                        "category": cat, "district": item["label"] if item["key"] == "district" else params.get("district", "Bengaluru Urban")}
                       for p in res.forecast]
                results.append({"category": cat, "data": pts})
            return jsonify(results if len(loop) > 1 else results[0]["data"]), 200

        elif action == "get_offender_profile":
            name = params.get("name", "")
            profile = ai_handler.offender_profiler.get_profile(name)
            score = ai_handler.priority_scorer.calculate_score(profile.entity_id, name)
            return jsonify({
                "entity_name": name, "total_score": score.total_score, "risk_tier": score.risk_tier,
                "features": [{"name": f.name, "raw_value": f.raw_value, "normalized_value": f.normalized_value,
                              "weight": f.weight, "contribution": f.contribution} for f in score.features],
                "linked_cases": [{"case_id": c.get("case_id"), "crime_no": c.get("crime_no"),
                                  "crime_type": c.get("crime_type"), "year": c.get("year"),
                                  "status": c.get("status", "Under Investigation")} for c in profile.linked_cases],
                "disclaimer": score.disclaimer
            }), 200

        elif action == "create_offender_profile":
            row_data = {
                "AccusedMasterID": params.get("accused_master_id", 1),
                "CaseMasterID": int(params.get("case_master_id", 0)),
                "AccusedName": params.get("accused_name", ""),
                "AgeYear": int(params.get("age_year", 0)),
                "GenderID": int(params.get("gender_id", 1)),
                "PersonID": params.get("person_id", "A1")
            }
            res = ai_handler._db_client.insert_bulk_rows("Accused", [row_data])
            return jsonify(res), 200

        elif action == "get_trends":
            types = ['Theft', 'Robbery', 'Assault', 'Burglary', 'Cyber Crime']
            points = []
            for t in types:
                req = CrimeTrendRequestDTO(crime_sub_head_id=1, district_id=None, start_date=None, end_date=None)
                res = ai_handler.trends.analyze(req)
                for p in res.aggregation:
                    points.append({"period": p["period"], "count": p["count"],
                                   "pct_change": p["pct_change"], "crime_type": t})
            return jsonify(points), 200

        elif action == "get_hotspots":
            req = HotspotRequestDTO(district_id=params.get("district_id", 1),
                                    crime_sub_head_id=None, eps_km=1.0, min_cases=5)
            res = ai_handler.hotspots.detect(req)
            return jsonify([{"cluster_id": c.cluster_id, "centroid_lat": c.centroid_lat,
                             "centroid_lng": c.centroid_lng, "case_count": c.case_count,
                             "radius_km": c.radius_km, "crime_type": c.crime_type}
                            for c in res.clusters]), 200

        elif action == "get_network":
            res = ai_handler.graph_projector.build_graph(params.get("accused_name", ""), params.get("depth", 2))
            return jsonify({
                "nodes": [{"id": n.id, "label": n.label, "node_type": n.node_type,
                           "cases": n.cases, "risk_tier": n.risk_tier} for n in res.nodes],
                "edges": [{"id": e.id, "source": e.source, "target": e.target,
                           "weight": e.weight, "shared_cases": e.shared_cases} for e in res.edges]
            }), 200

        elif action == "get_dashboard_kpis":
            stats = ai_handler.stats.get_dashboard_stats()
            return jsonify([
                {'label': 'Total FIRs', 'value': f"{stats.total_cases:,}", 'change': '+12.4%', 'icon': 'FileText'},
                {'label': 'Active Cases', 'value': f"{stats.pending_cases:,}", 'change': '-8.2%', 'icon': 'Activity'},
                {'label': 'Clearance Rate', 'value': f"{100 - stats.heinous_pct}%", 'change': '+3.1%', 'icon': 'CheckCircle'},
                {'label': 'Districts Covered', 'value': str(stats.district_count), 'change': '+0', 'icon': 'MapPin'},
            ]), 200

        elif action == "get_alerts":
            return jsonify([{
                "id": a.alert_id, "severity": a.severity, "title": a.title,
                "description": a.description, "rule_id": a.rule_id,
                "trigger_condition": a.triggering_condition, "created_at": a.created_at, "acknowledged": False
            } for a in ai_handler.alerts.evaluate()]), 200

        elif action == "import_table":
            table_name = params.get("table_name", "")
            rows = params.get("rows", [])
            if not table_name or not rows:
                return jsonify({"error": "INVALID_PARAMS", "message": "table_name and rows required"}), 400
            return jsonify(ai_handler._db_client.insert_bulk_rows(table_name, rows)), 200

        elif action == "run_sql":
            if not app:
                return jsonify({"error": "SDK_NOT_INITIALIZED"}), 500
            sql = params.get("sql", "")
            if not sql:
                return jsonify({"error": "sql required"}), 400
            return jsonify(ai_handler._db_client.execute_non_query(sql)), 200

        elif action == "describe_table":
            if not app:
                return jsonify({"error": "SDK_NOT_INITIALIZED"}), 500
            tbl = app.datastore().table(params.get("table_name", ""))
            names = []
            for c in tbl.get_all_columns():
                d = c.to_dict() if hasattr(c, 'to_dict') else c
                names.append(d.get("column_name", ""))
            return jsonify({"columns": names}), 200

        else:
            return jsonify({"error": "UNKNOWN_ACTION", "message": f"Action '{action}' is not supported."}), 400

    except Exception as e:
        logger.exception("Error handling request action: %s", action)
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500
