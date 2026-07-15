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

    # RBAC authorization check
    if user_context and action not in ("login",):
        if not ai_handler.rbac.authorize_action(user_context, action):
            ai_handler.audit.log(user_context, action, params, "denied")
            return jsonify({"error": "FORBIDDEN", "message": f"Role '{user_context.role_name}' cannot perform '{action}'."}), 403

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
            ai_handler.audit.log(user_context, action, {"message_len": len(message)}, "success")
            return jsonify({
                "message_id": result.message_id, "message_type": result.message_type,
                "content_text": result.content_text, "content_kannada": result.content_kannada or "",
                "sql_text": result.sql_text, "chart_recommendation": result.chart_recommendation,
                "evidence_refs": [e.model_dump() for e in result.evidence_refs],
                "confidence_class": result.confidence_class,
                "suggested_followups": result.suggested_followups,
                "data_quality_warnings": result.data_quality_warnings or [],
                "tool_params": result.tool_params or {},
                "created_at": result.created_at or datetime.utcnow().isoformat()
            }), 200

        elif action == "login":
            req = LoginRequestDTO(kgid=params.get("kgid", ""), password=params.get("password", ""))
            res = ai_handler.auth.login(req)
            return jsonify(res), 200

        elif action == "verify_token":
            token = params.get("token", "")
            uc = ai_handler.auth.verify_token(token)
            if not uc:
                return jsonify({"error": "INVALID_TOKEN"}), 401
            return jsonify({"user": uc.model_dump()}), 200

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
            ai_handler.audit.log(user_context, action, {}, "success")
            return jsonify(results if len(loop) > 1 else results[0]["data"]), 200

        elif action == "get_offender_profile":
            name = params.get("name", "")
            profile = ai_handler.offender_profiler.get_profile(name)
            score = ai_handler.priority_scorer.calculate_score(profile.entity_id, name)
            result = {
                "entity_name": name, "total_score": score.total_score, "risk_tier": score.risk_tier,
                "features": [{"name": f.name, "raw_value": f.raw_value, "normalized_value": f.normalized_value,
                              "weight": f.weight, "contribution": f.contribution} for f in score.features],
                "linked_cases": [{"case_id": c.get("case_id"), "crime_no": c.get("crime_no"),
                                  "crime_type": c.get("crime_type"), "year": c.get("year"),
                                  "status": c.get("status", "Under Investigation")} for c in profile.linked_cases],
                "disclaimer": score.disclaimer
            }
            # PII masking for non-authorized roles
            result = ai_handler.rbac.mask_pii(result, user_context.role_name) if user_context else result
            ai_handler.audit.log(user_context, action, {"name": name}, "success")
            return jsonify(result), 200

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
            ai_handler.audit.log(user_context, action, {"table": "Accused"}, "success")
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
            alerts = ai_handler.alerts.evaluate(params.get("district_id"))
            return jsonify([{
                "id": a.alert_id, "severity": a.severity, "title": a.title,
                "description": a.description, "rule_id": a.rule_id,
                "trigger_condition": a.triggering_condition, "created_at": a.created_at,
                "acknowledged": False, "evidence": a.evidence,
            } for a in alerts]), 200

        elif action == "acknowledge_alert":
            alert_id = params.get("alert_id", "")
            ai_handler.audit.log(user_context, action, {"alert_id": alert_id}, "success")
            return jsonify({"status": "acknowledged", "alert_id": alert_id}), 200

        elif action == "import_table":
            table_name = params.get("table_name", "")
            rows = params.get("rows", [])
            if not table_name or not rows:
                return jsonify({"error": "INVALID_PARAMS", "message": "table_name and rows required"}), 400
            # RBAC row-scope enforcement: only allow import to tables in user's scope
            scope = ai_handler.rbac.row_filter_clause(user_context) if user_context else ""
            if scope:
                logger.info("RBAC scope applied to import_table: %s", scope)
            return jsonify(ai_handler._db_client.insert_bulk_rows(table_name, rows)), 200

        elif action == "run_sql":
            if not app:
                return jsonify({"error": "SDK_NOT_INITIALIZED"}), 500
            sql = params.get("sql", "")
            if not sql:
                return jsonify({"error": "sql required"}), 400
            # RBAC row-scope: wrap non-DDL queries with filter
            scope = ai_handler.rbac.row_filter_clause(user_context) if user_context else ""
            if scope and sql.strip().upper().startswith("SELECT"):
                if "WHERE" in sql.upper():
                    sql = sql.replace("WHERE ", f"WHERE {scope} AND ", 1)
                else:
                    idx = sql.upper().rfind("LIMIT")
                    if idx > 0:
                        sql = sql[:idx] + f" WHERE {scope} " + sql[idx:]
                    else:
                        sql += f" WHERE {scope}"
            ai_handler.audit.log(user_context, action, {"sql_len": len(sql)}, "success")
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

        elif action == "list_audit_log":
            limit = params.get("limit", 100)
            event_type = params.get("event_type")
            category = params.get("category")
            actor = params.get("actor")
            return jsonify(ai_handler.audit.get_recent(limit, event_type, category, actor)), 200

        elif action == "commander_query":
            query = params.get("query", "")
            result = ai_handler.commander.run(query, user_context)
            ai_handler.audit.log(user_context, action, {"query_len": len(query)}, "success")
            return jsonify(result), 200

        # ── Investigation Suite ───────────────────────────────────────────
        elif action == "create_investigation":
            inv = ai_handler.investigations.create(
                params.get("title", ""), params.get("description", ""), user_context.user_id
            )
            ai_handler.audit.log(user_context, action, {"title": inv.title}, "success")
            return jsonify(inv.model_dump()), 200

        elif action == "list_investigations":
            return jsonify(ai_handler.investigations.list_all()), 200

        elif action == "get_investigation":
            result = ai_handler.investigations.get(params.get("investigation_id", ""))
            if not result:
                return jsonify({"error": "NOT_FOUND"}), 404
            return jsonify(result), 200

        elif action == "add_case_to_investigation":
            ok = ai_handler.investigations.add_case(
                params.get("investigation_id", ""), params.get("case_master_id", 0),
                params.get("notes", "")
            )
            if not ok:
                return jsonify({"error": "NOT_FOUND"}), 404
            return jsonify({"status": "ok"}), 200

        elif action == "add_graph_to_investigation":
            saved = ai_handler.investigations.add_graph(
                params.get("investigation_id", ""), params.get("graph_data", {}),
                params.get("label", "")
            )
            if not saved:
                return jsonify({"error": "NOT_FOUND"}), 404
            return jsonify(saved.model_dump()), 200

        elif action == "get_case_similarity":
            return jsonify([s.model_dump() for s in ai_handler.similarity.find_similar(
                params.get("case_master_id", 0), params.get("top_k", 5)
            )]), 200

        elif action == "get_case_timeline":
            return jsonify([t.model_dump() for t in ai_handler.timeline.generate(
                params.get("case_master_id", 0)
            )]), 200

        elif action == "get_case_leads":
            return jsonify([l.model_dump() for l in ai_handler.leads.generate_leads(
                params.get("case_master_id", 0)
            )]), 200

        elif action == "generate_investigation_report":
            inv_data = ai_handler.investigations.get(params.get("investigation_id", ""))
            if not inv_data:
                return jsonify({"error": "NOT_FOUND"}), 404
            report = ai_handler.inv_reports.generate(params["investigation_id"], inv_data)
            return jsonify(report.model_dump()), 200

        # ── AI Governance — Phase 5 ────────────────────────────────────
        elif action == "list_models":
            return jsonify([m.model_dump() for m in ai_handler.model_registry.list_all()]), 200

        elif action == "register_model":
            entry = ai_handler.model_registry.register(
                params.get("model_name", ""), params.get("model_version", ""),
                params.get("provider", ""), params.get("capabilities"),
                params.get("parameters"),
            )
            ai_handler.audit.log(user_context, action, {"model_id": entry.model_id}, "success")
            return jsonify(entry.model_dump()), 200

        elif action == "list_prompts":
            return jsonify([p.model_dump() for p in ai_handler.prompt_registry.list_all()]), 200

        elif action == "register_prompt":
            entry = ai_handler.prompt_registry.register(
                params.get("prompt_name", ""), params.get("prompt_version", ""),
                params.get("prompt_text", ""), params.get("model_id"),
            )
            ai_handler.audit.log(user_context, action, {"prompt_id": entry.prompt_id}, "success")
            return jsonify(entry.model_dump()), 200

        elif action == "list_agent_capabilities":
            return jsonify([a.model_dump() for a in ai_handler.agent_capabilities.list_all()]), 200

        elif action == "list_executions":
            mission_id = params.get("mission_id", "")
            if mission_id:
                return jsonify([e.model_dump() for e in ai_handler.execution_tracker.list_by_mission(mission_id)]), 200
            return jsonify({"error": "mission_id required"}), 400

        elif action == "list_missions":
            return jsonify([m.model_dump() for m in ai_handler.mission_tracker.list_missions()]), 200

        elif action == "get_mission":
            mission = ai_handler.mission_tracker.get_mission(params.get("mission_id", ""))
            if not mission:
                return jsonify({"error": "NOT_FOUND"}), 404
            tasks = ai_handler.mission_tracker.list_tasks(mission.mission_id)
            return jsonify({"mission": mission.model_dump(), "tasks": [t.model_dump() for t in tasks]}), 200

        elif action == "list_claims":
            return jsonify([c.model_dump() for c in ai_handler.claim_ledger.list_all()]), 200

        elif action == "add_claim":
            entry = ai_handler.claim_ledger.add_entry(
                params.get("statement", ""), params.get("classification", "DATABASE_FACT"),
                params.get("producer", ""), params.get("model_version"),
                params.get("evidence_refs"), params.get("confidence", 1.0),
                params.get("source_execution_id"),
            )
            ai_handler.audit.log(user_context, action, {"claim_id": entry.claim_id}, "success")
            return jsonify(entry.model_dump()), 200

        elif action == "update_claim_status":
            ok = ai_handler.claim_ledger.update_status(
                params.get("claim_id", ""), params.get("status", "Under Review")
            )
            if not ok:
                return jsonify({"error": "NOT_FOUND"}), 404
            return jsonify({"status": "ok"}), 200

        # ── Communication & Resource Sharing ──────────────────────────
        elif action == "send_message":
            msg = ai_handler.messages.send(
                params.get("type", "STATUS_UPDATE"),
                user_context.user_id if user_context else 0,
                user_context.role_name if user_context else "Constable",
                params.get("unit_id", 0), params.get("unit_name", ""),
                params.get("to_ids", []), params.get("subject", ""),
                params.get("body", ""), params.get("cc_ids"),
                params.get("linked_resources"), params.get("attachments"),
                params.get("priority", "NORMAL"), params.get("parent_message_id"),
            )
            ai_handler.audit.log(user_context, action, {"message_id": msg.message_id}, "success")
            return jsonify(msg.model_dump()), 200

        elif action == "list_inbox":
            return jsonify([m.model_dump() for m in ai_handler.messages.list_inbox(
                params.get("employee_id", 0),
                params.get("unread_only", False),
                params.get("priority_filter"),
                params.get("since"),
            )]), 200

        elif action == "get_message":
            msg = ai_handler.messages.get(params.get("message_id", ""))
            if not msg:
                return jsonify({"error": "NOT_FOUND"}), 404
            return jsonify(msg.model_dump()), 200

        elif action == "mark_read":
            mid = params.get("message_id", "")
            ok = ai_handler.messages.mark_read(mid, params.get("employee_id", 0))
            ai_handler.audit.log(user_context, action, {"message_id": mid, "detail": f"Message {mid} marked read"}, "success" if ok else "skipped")
            return jsonify({"ok": ok}), 200

        elif action == "acknowledge_message":
            mid = params.get("message_id", "")
            ok = ai_handler.messages.acknowledge(mid, params.get("employee_id", 0))
            ai_handler.audit.log(user_context, action, {"message_id": mid, "detail": f"Message {mid} acknowledged"}, "success" if ok else "skipped")
            return jsonify({"ok": ok}), 200

        elif action == "get_thread":
            return jsonify([m.model_dump() for m in ai_handler.messages.get_thread(params.get("message_id", ""))]), 200

        elif action == "list_all_messages":
            return jsonify([m.model_dump() for m in ai_handler.messages.list_all()]), 200

        elif action == "check_permission":
            user_scope = params.get("scope", "own_station")
            rt = params.get("resource_type", "")
            act = params.get("action", "")
            result = ai_handler.permissions.check(
                params.get("rank", ""), rt, act, user_scope,
            )
            ai_handler.audit.log(user_context, action, {"resource_type": rt, "resource_id": act, "detail": f"Check {rt}:{act}={result.allowed}"}, "allowed" if result.allowed else "denied")
            return jsonify(result.model_dump()), 200

        elif action == "get_effective_permissions":
            return jsonify(ai_handler.permissions.get_effective(
                params.get("rank", ""), params.get("resource_type", "")
            )), 200

        elif action == "delegate_permission":
            entry = ai_handler.permissions.delegate(
                params.get("grantor_id", 0), params.get("grantee_id", 0),
                params.get("permission", ""), params.get("scope", "own_station"),
                params.get("valid_until"), params.get("reason", ""),
            )
            ai_handler.audit.log(user_context, action, {"permission_id": entry.permission_id}, "success")
            return jsonify(entry.model_dump()), 200

        elif action == "revoke_delegation":
            pid = params.get("permission_id", "")
            ok = ai_handler.permissions.revoke_delegation(pid)
            ai_handler.audit.log(user_context, action, {"permission_id": pid, "detail": f"Delegation {pid} revoked"}, "success" if ok else "not_found")
            return jsonify({"ok": ok}), 200

        elif action == "list_delegations":
            return jsonify([d.model_dump() for d in ai_handler.permissions.list_delegations(
                params.get("grantor_id"), params.get("grantee_id"),
            )]), 200

        elif action == "set_emergency":
            ai_handler.permissions.set_emergency(
                params.get("active", False), params.get("duration_hours", 72)
            )
            ai_handler.audit.log(user_context, action, {"active": params.get("active")}, "success")
            return jsonify({"status": "ok", "emergency": ai_handler.permissions.is_emergency}), 200

        elif action == "get_emergency_status":
            return jsonify({"emergency": ai_handler.permissions.is_emergency}), 200

        elif action == "create_org_group":
            g = ai_handler.groups.create_org_group(
                params.get("name", ""), params.get("group_type", "STATION"),
                params.get("parent_id"),
            )
            ai_handler.audit.log(user_context, action, {"group_id": g.group_id}, "success")
            return jsonify(g.model_dump()), 200

        elif action == "list_org_groups":
            return jsonify([g.model_dump() for g in ai_handler.groups.list_org_groups(
                params.get("group_type")
            )]), 200

        elif action == "create_dynamic_group":
            dissolve_h = params.get("dissolve_hours")
            duration_days = dissolve_h / 24 if dissolve_h else params.get("duration_days", 90)
            g = ai_handler.groups.create_dynamic_group(
                params.get("name", ""), params.get("group_type", "TASK_FORCE"),
                params.get("lead_id", 0), params.get("case_ids"),
                params.get("offender_ids"), duration_days, params.get("description"),
            )
            ai_handler.audit.log(user_context, action, {"group_id": g.group_id, "detail": f"Created group {g.group_name}"}, "success")
            return jsonify(g.model_dump()), 200

        elif action == "list_dynamic_groups":
            return jsonify([g.model_dump() for g in ai_handler.groups.list_dynamic_groups(
                params.get("active_only", True)
            )]), 200

        elif action == "dissolve_group":
            gid = params.get("group_id", "")
            ok = ai_handler.groups.dissolve_group(gid)
            ai_handler.audit.log(user_context, action, {"group_id": gid, "detail": f"Group {gid} dissolved"}, "success" if ok else "not_found")
            return jsonify({"ok": ok}), 200

        elif action == "add_group_member":
            gid = params.get("group_id", "")
            eid = params.get("employee_id", 0)
            role = params.get("role_in_group") or params.get("role", "MEMBER")
            m = ai_handler.groups.add_group_member(
                gid, eid,
                role, params.get("can_modify", False),
                params.get("can_approve", False), params.get("data_scope", "group"),
            )
            if not m:
                return jsonify({"error": "NOT_FOUND"}), 404
            ai_handler.audit.log(user_context, action, {"group_id": gid, "resource_id": str(eid), "detail": f"Added #{eid} to group {gid}"}, "success")
            return jsonify(m.model_dump()), 200

        elif action == "remove_group_member":
            gid = params.get("group_id", "")
            eid = params.get("employee_id", 0)
            ok = ai_handler.groups.remove_group_member(gid, eid)
            ai_handler.audit.log(user_context, action, {"group_id": gid, "resource_id": str(eid), "detail": f"Removed #{eid} from group {gid}"}, "success" if ok else "not_found")
            return jsonify({"ok": ok}), 200

        elif action == "list_group_members":
            return jsonify([m.model_dump() for m in ai_handler.groups.list_members(
                params.get("group_id", "")
            )]), 200

        elif action == "list_my_groups":
            return jsonify([g.model_dump() for g in ai_handler.groups.list_groups_for_employee(
                params.get("employee_id", 0)
            )]), 200

        elif action == "create_coordination":
            req = ai_handler.groups.create_coordination(
                params.get("from_id", 0), params.get("to_unit_id", 0),
                params.get("request_type", "SUSPECT_LOCATION"),
                params.get("subject", ""), params.get("body", ""),
                params.get("case_id"),
            )
            ai_handler.audit.log(user_context, action, {"request_id": req.request_id}, "success")
            return jsonify(req.model_dump()), 200

        elif action == "update_coordination":
            rid = params.get("request_id", "")
            st = params.get("status", "")
            ok = ai_handler.groups.update_coordination(rid, st, params.get("assigned_to"))
            ai_handler.audit.log(user_context, action, {"request_id": rid, "detail": f"Coordination {rid} → {st}"}, "success" if ok else "not_found")
            return jsonify({"ok": ok}), 200

        elif action == "list_coordination":
            return jsonify([r.model_dump() for r in ai_handler.groups.list_coordination(
                params.get("from_id"), params.get("to_unit"), params.get("status"),
            )]), 200

        # ── Technical Support Engineer — Diagnostics ────────────────────
        elif action == "tse_schema_tables":
            return jsonify(ai_handler.tse.schema_tables()), 200

        elif action == "tse_schema_columns":
            tbl = params.get("table_name", "")
            if not tbl:
                return jsonify({"error": "table_name required"}), 400
            if not ai_handler.rbac.table_access_allowed(user_context.role_name, tbl) if user_context else True:
                return jsonify({"error": "TABLE_DENIED", "message": f"Table '{tbl}' is denied for role '{user_context.role_name}'."}), 403
            return jsonify(ai_handler.tse.schema_columns(tbl)), 200

        elif action == "tse_constraint_check":
            return jsonify(ai_handler.tse.constraint_check()), 200

        elif action == "tse_system_metrics":
            return jsonify(ai_handler.tse.system_metrics()), 200

        elif action == "tse_active_sessions":
            return jsonify(ai_handler.tse.active_sessions()), 200

        elif action == "tse_index_stats":
            return jsonify(ai_handler.tse.index_stats()), 200

        elif action == "tse_error_logs":
            return jsonify(ai_handler.tse.error_logs(params.get("limit", 20))), 200

        elif action == "tse_cache_stats":
            return jsonify(ai_handler.tse.cache_stats()), 200

        elif action == "tse_auth_tokens":
            return jsonify(ai_handler.tse.auth_tokens()), 200

        elif action == "tse_validate_sql":
            sql = params.get("sql", "")
            if not sql:
                return jsonify({"error": "sql required"}), 400
            return jsonify(ai_handler.tse.validate_sql(sql)), 200

        else:
            return jsonify({"error": "UNKNOWN_ACTION", "message": f"Action '{action}' is not supported."}), 400

    except Exception as e:
        logger.exception("Error handling request action: %s", action)
        if user_context:
            ai_handler.audit.log(user_context, action, params, f"error: {str(e)}")
        return jsonify({"error": "INTERNAL_SERVER_ERROR", "message": str(e)}), 500
