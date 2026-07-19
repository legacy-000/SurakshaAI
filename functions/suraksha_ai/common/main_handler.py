import logging

from common.auth.auth_handler import AuthHandler
from common.chat.chat_handler import ChatHandler
from common.analytics.trend_analyzer import TrendAnalyzer
from common.analytics.hotspot_detector import HotspotDetector
from common.analytics.stats_aggregator import StatsAggregator
from common.network.graph_projector import GraphProjector
from common.offender.offender_profiler import OffenderProfiler
from common.offender.priority_scorer import PriorityScorer
from common.forecast.forecaster import Forecaster, build_forecaster
from common.forecast.alert_engine import AlertEngine
from common.db.datastore_client import DatastoreClient
from common.security.rbac_middleware import RBACMiddleware
from common.security.audit_logger import AuditLogger
from common.ai.quickml_client import QuickMLClient
from common.commander.commander import Commander
from common.commander.database_agent import DatabaseAgent
from common.commander.trend_agent import TrendAgent
from common.commander.geospatial_agent import GeospatialAgent
from common.commander.offender_agent import OffenderAgent
from common.commander.evidence_validator import EvidenceValidator
from common.investigation.investigation_manager import InvestigationManager
from common.investigation.similarity_engine import SimilarityEngine
from common.investigation.timeline_generator import TimelineGenerator
from common.investigation.lead_generator import LeadGenerator
from common.investigation.report_generator import ReportGenerator as InvReportGenerator
from common.governance.governance import (
    ModelRegistry, PromptRegistry, AgentCapabilityRegistry,
    AgentExecutionTracker, MissionTracker, ClaimLedger,
)
from common.comms.message_engine import MessageEngine
from common.comms.permission_engine import PermissionEngine
from common.comms.group_manager import GroupManager
from common.support.tse_handler import TSEHandler

logger = logging.getLogger(__name__)


class SurakshaAIHandler:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app
        self._db_client = DatastoreClient(self._catalyst_app)
        self.quickml = QuickMLClient(self._catalyst_app)

        self.auth = AuthHandler(self._catalyst_app)
        self.chat = ChatHandler(self._catalyst_app)
        self.trends = TrendAnalyzer()
        self.hotspots = HotspotDetector()
        self.stats = StatsAggregator()
        self.graph_projector = GraphProjector()
        self.offender_profiler = OffenderProfiler()
        self.priority_scorer = PriorityScorer()
        self.forecaster = build_forecaster()
        self.alerts = AlertEngine()
        self.rbac = RBACMiddleware(self._db_client)
        self.audit = AuditLogger(self._db_client)
        self.evidence_validator = EvidenceValidator()

        # Investigation Suite
        self.investigations = InvestigationManager()
        self.similarity = SimilarityEngine(self.quickml, self._db_client)
        self.timeline = TimelineGenerator()
        self.leads = LeadGenerator()
        self.inv_reports = InvReportGenerator()

        # AI Governance — Phase 5
        self.model_registry = ModelRegistry()
        self.prompt_registry = PromptRegistry()
        self.agent_capabilities = AgentCapabilityRegistry()
        self.execution_tracker = AgentExecutionTracker()
        self.mission_tracker = MissionTracker(self.execution_tracker)
        self.claim_ledger = ClaimLedger()

        # Communication & Resource Sharing
        self.messages = MessageEngine(self._db_client)
        self.permissions = PermissionEngine(self._db_client)
        self.groups = GroupManager(self._db_client)

        # Technical Support Engineer — diagnostics
        self.tse = TSEHandler(self._db_client, self._catalyst_app)

        # Commander + agents
        self._build_container()

        self.commander = Commander(self.evidence_validator)
        self.commander.register_agent("database_query", DatabaseAgent(self.chat, self._db_client))
        self.commander.register_agent("trend_analysis", TrendAgent(self.trends))
        self.commander.register_agent("geospatial_analysis", GeospatialAgent(self.hotspots))
        self.commander.register_agent("offender_profile", OffenderAgent(self.offender_profiler, self.priority_scorer))

        # Seed governance registries with known agents
        self.agent_capabilities.register("database_query",
                                         ["database_query",
                                          "case_lookup",
                                          "evidence_search"],
                                         "Query the FIR database for case details, offender records, and evidence.",
                                         ["chat_query"])
        self.agent_capabilities.register("trend_analysis", ["trend_analysis", "pattern_analysis"],
                                         "Analyze crime trends and detect patterns over time.", ["view_trends"])
        self.agent_capabilities.register("geospatial_analysis",
                                         ["geospatial_analysis",
                                          "hotspot_detection"],
                                         "Detect crime hotspots and analyze geographic crime patterns.",
                                         ["view_geospatial"])
        self.agent_capabilities.register("offender_profile", ["offender_profile", "priority_scoring"],
                                         "Build offender profiles and compute priority risk scores.", ["view_offender"])

    @property
    def is_live(self):
        return self._catalyst_app is not None

    def _build_container(self):
        """Wire repo abstractions into services that already accept them (Part E.5 DIP)."""
        from common.repositories.zcql_impl import (
            ZCQLCaseRepository, ZCQLAccusedRepository, CatalystRowPrecomputedStore,
        )
        from common.offender.entity_resolver import build_entity_resolver
        cr = ZCQLCaseRepository(self._db_client)
        ar = ZCQLAccusedRepository(self._db_client)
        st = CatalystRowPrecomputedStore(self._db_client)
        self.trends = TrendAnalyzer(case_repo=cr, store=st)
        self.hotspots = HotspotDetector(case_repo=cr, store=st)
        self.offender_profiler = OffenderProfiler(accused_repo=ar)
        self.resolver = build_entity_resolver(store=st)


# ---------------------------------------------------------------------------
# Action dispatch table (Part G: thin Controller).
#
# Each action is a small module-level function. They take the composed
# handler instance plus the parsed request context and return either a
# tuple ``(payload, status)`` or a bare payload (status defaults to 200).
# main.py's ``handler()`` does only RBAC gating, dispatch, and response
# shaping — no business logic lives in main.py anymore.
# ---------------------------------------------------------------------------
from datetime import datetime  # noqa: E402  (kept here to avoid reordering existing imports)

from common.models.dto import (
    LoginRequestDTO, QueryRequestDTO, CrimeTrendRequestDTO, HotspotRequestDTO,
    ForecastRequestDTO,
)  # noqa: E402


def _ctx(action, handler, user_context, params, body=None):
    """Per-request context bundle passed to every action handler."""
    return {
        "handler": handler, "user_context": user_context,
        "params": params, "body": body or {}, "action": action,
    }


def h_login(c):
    req = LoginRequestDTO(kgid=c["params"].get("kgid", ""),
                          password=c["params"].get("password", ""))
    return c["handler"].auth.login(req)


def h_verify_token(c):
    token = c["params"].get("token", "")
    uc = c["handler"].auth.verify_token(token)
    if not uc:
        return ({"error": "INVALID_TOKEN"}, 401)
    return {"user": uc.model_dump()}


def h_chat_query(c):
    message = c["params"].get("message", c["params"].get("query", ""))
    req = QueryRequestDTO(message=message, lang=c["params"].get("lang", "en"))
    result = c["handler"].chat.handle_query(req, c["user_context"])
    return {
        "message_id": result.message_id, "message_type": result.message_type,
        "content_text": result.content_text,
        "content_kannada": result.content_kannada or "",
        "sql_text": result.sql_text,
        "chart_recommendation": result.chart_recommendation,
        "evidence_refs": [e.model_dump() for e in result.evidence_refs],
        "confidence_class": result.confidence_class,
        "suggested_followups": result.suggested_followups,
        "data_quality_warnings": result.data_quality_warnings or [],
        "tool_params": result.tool_params or {},
        "created_at": result.created_at or datetime.utcnow().isoformat(),
    }


def h_get_crime_stats(c):
    # Same internal path as chat_query when no NL message; wrapper kept
    # for the original action contract.
    return h_chat_query(c)


def h_get_forecast(c):
    p = c["params"]
    req = ForecastRequestDTO(
        district_id=p.get("district_id", 1),
        crime_sub_head_id=p.get("crime_sub_head_id", 1),
        forecast_horizon_days=30, training_window_days=365
    )
    categories = p.get("categories")
    districts = p.get("districts")
    results = []
    loop = [{"label": c, "key": "category"} for c in (categories or [p.get("category", "Theft")])] + \
           [{"label": d, "key": "district"} for d in (districts or [])]
    for item in loop:
        if item["key"] == "district":
            req.district_id = p.get("district_id", 1)
            cat = p.get("category", "Theft")
        else:
            cat = item["label"]
        res = c["handler"].forecaster.forecast(req, db=c["handler"]._db_client)
        pts = [{"date": p.date, "predicted": p.predicted, "upper": p.upper,
                "lower": p.lower, "category": cat,
                "district": item["label"] if item["key"] == "district" else p.get("district", "Bengaluru Urban")}
               for p in res.forecast]
        results.append({"category": cat, "data": pts})
    return results[0]["data"] if len(loop) <= 1 else results


def h_get_offender_profile(c):
    name = c["params"].get("name", "")
    h = c["handler"]
    profile = h.offender_profiler.get_profile(name)
    score = h.priority_scorer.calculate_score(profile.entity_id, name)
    result = {
        "entity_name": name, "total_score": score.total_score,
        "risk_tier": score.risk_tier,
        "features": [{"name": f.name, "raw_value": f.raw_value,
                      "normalized_value": f.normalized_value, "weight": f.weight,
                      "contribution": f.contribution} for f in score.features],
        "linked_cases": [{"case_id": c.get("case_id"), "crime_no": c.get("crime_no"),
                          "crime_type": c.get("crime_type"), "year": c.get("year"),
                          "status": c.get("status", "Under Investigation")}
                         for c in profile.linked_cases],
        "disclaimer": score.disclaimer,
    }
    if c["user_context"]:
        result = h.rbac.mask_pii(result, c["user_context"].role_name)
    return result


def h_create_offender_profile(c):
    p = c["params"]
    row_data = {
        "AccusedMasterID": p.get("accused_master_id", 1),
        "CaseMasterID": int(p.get("case_master_id", 0)),
        "AccusedName": p.get("accused_name", ""),
        "AgeYear": int(p.get("age_year", 0)),
        "GenderID": int(p.get("gender_id", 1)),
        "PersonID": p.get("person_id", "A1"),
    }
    return c["handler"]._db_client.insert_bulk_rows("Accused", [row_data])


def _cached(key: str):
    try:
        return cache_get(key)
    except Exception:
        return None


def _store(key: str, data):
    try:
        cache_set(key, data)
    except Exception:
        pass


def h_get_trends(c):
    cached = _cached("trends")
    if cached is not None:
        return cached
    db = c["handler"]._db_client

    def _fetch_map(sql: str, key_col: str, val_col: str) -> dict:
        m = {}
        res = db.execute_non_query(sql)
        if "error" not in res:
            cols = res.get("columns", [])
            for row in res.get("rows", []):
                d = dict(zip(cols, row))
                k = str(d.get(key_col, ""))
                v = str(d.get(val_col, ""))
                if k and v:
                    m[k] = v
        return m

    sid_name = _fetch_map(
        "SELECT CrimeSubHeadID, CrimeHeadName FROM CrimeSubHead",
        "CrimeSubHeadID", "CrimeHeadName")

    res = db.execute_non_query(
        "SELECT CrimeRegisteredDate, CrimeMinorHeadID FROM CaseMaster "
        "WHERE CrimeRegisteredDate IS NOT NULL LIMIT 300")
    monthly: dict[str, dict[str, int]] = {}
    if "error" not in res:
        cols = res.get("columns", [])
        for row in res.get("rows", []):
            d = dict(zip(cols, row))
            sid = str(d.get("CrimeMinorHeadID", ""))
            ct = sid_name.get(sid, "Unknown")
            dt = str(d.get("CrimeRegisteredDate", ""))[:7]
            if len(dt) < 7:
                continue
            m = monthly.setdefault(dt, {})
            m[ct] = m.get(ct, 0) + 1
    sorted_months = sorted(monthly)
    points = []
    for i, m in enumerate(sorted_months):
        for ct, cnt in monthly[m].items():
            prev = monthly.get(sorted_months[i - 1], {}).get(ct) if i > 0 else None
            pct = round((cnt - prev) / prev * 100, 1) if prev and prev > 0 else None
            points.append({"period": m, "count": cnt, "pct_change": pct, "crime_type": ct})
    result = {"monthly": points}
    _store("trends", result)
    return result


def h_get_socio_demographics(c):
    try:
        return _h_get_socio_demographics(c)
    except Exception as e:
        import traceback
        logging.getLogger().error("demographics error: %s\n%s", e, traceback.format_exc())
        return {"error": str(e), "_v": "5"}


def _h_get_socio_demographics(c):
    cached = _cached("socio_demographics")
    if cached is not None and cached.get("_v") == "5":
        return cached
    db = c["handler"]._db_client
    out: dict = {"_v": "5"}

    def _fetch_map(sql, kcol, vcol):
        m = {}
        res = db.execute_non_query(sql)
        if "error" not in res:
            cols = res.get("columns", [])
            for row in res.get("rows", []):
                d = dict(zip(cols, row))
                k = d.get(kcol)
                if k is not None:
                    m[str(k)] = str(d.get(vcol, ""))
        return m

    out["occupations"] = _fetch_map(
        "SELECT OccupationID, OccupationName FROM OccupationMaster LIMIT 500", "OccupationID", "OccupationName")
    out["religions"] = _fetch_map(
        "SELECT ReligionID, ReligionName FROM ReligionMaster LIMIT 500", "ReligionID", "ReligionName")
    sid_name = _fetch_map(
        "SELECT CrimeSubHeadID, CrimeHeadName FROM CrimeSubHead LIMIT 500", "CrimeSubHeadID", "CrimeHeadName")

    def _fmt(res):
        if "error" in res:
            return []
        cols = res.get("columns", [])
        return [dict(zip(cols, row)) for row in res.get("rows", [])]

    def _id(v):
        if v is None:
            return ""
        s = str(v).strip()
        if s.endswith(".0"):
            s = s[:-2]
        return s

    # Fetch records with LIMIT on every query
    v_raw = _fmt(db.execute_non_query(
        "SELECT CaseMasterID, AgeYear, GenderID, VictimPolice FROM Victim WHERE AgeYear IS NOT NULL LIMIT 300"))
    a_raw = _fmt(db.execute_non_query(
        "SELECT CaseMasterID, AgeYear, GenderID FROM Accused WHERE AgeYear IS NOT NULL LIMIT 300"))
    c_raw = _fmt(db.execute_non_query(
        "SELECT CaseMasterID, AgeYear, GenderID, OccupationID, ReligionID FROM ComplainantDetails LIMIT 300"))

    # CaseMaster scan — ROWID is the primary key (CaseMasterID in other tables is foreign key to ROWID)
    cm_raw = db.execute_non_query(
        "SELECT ROWID, CrimeMinorHeadID, CrimeRegisteredDate FROM CaseMaster LIMIT 300")
    cm_rows = _fmt(cm_raw)

    # Build ROWID → CrimeMinorHeadID map + cases_by_year
    cm_map: dict[str, str] = {}
    years: dict[str, dict[str, int]] = {}
    for d in cm_rows:
        cid = _id(d.get("ROWID"))
        mid = _id(d.get("CrimeMinorHeadID", ""))
        if cid and mid:
            cm_map[cid] = mid
        dt = str(d.get("CrimeRegisteredDate", ""))
        if dt:
            y = dt[:4] if len(dt) >= 4 else "unknown"
            ct = sid_name.get(mid, "Unknown")
            yy = years.setdefault(y, {})
            yy[ct] = yy.get(ct, 0) + 1

    # Check overlap: which CaseMasterID values from records exist in the cm_map
    v_ids = {_id(r.get("CaseMasterID", "")) for r in v_raw if r.get("CaseMasterID")}
    a_ids = {_id(r.get("CaseMasterID", "")) for r in a_raw if r.get("CaseMasterID")}
    c_ids = {_id(r.get("CaseMasterID", "")) for r in c_raw if r.get("CaseMasterID")}
    all_victim_ids = v_ids | a_ids | c_ids
    hits = len(all_victim_ids & set(cm_map.keys()))
    missed = all_victim_ids - set(cm_map.keys())
    
    out["_debug"] = {
        "v": len(v_raw), "a": len(a_raw), "c": len(c_raw), "cm": len(cm_rows), "map": len(cm_map),
        "uniq_ids": len(all_victim_ids), "hits": hits, "miss": len(missed),
        "cm_keys": list(set(cm_map.keys()))[:3], "v_ids": list(all_victim_ids)[:3]
    }

    # Add crime_type to each record
    def _build(rows, cm_key):
        for r in rows:
            cid = _id(r.get(cm_key, ""))
            mid = cm_map.get(cid, "")
            r["crime_type"] = sid_name.get(mid, "Unknown")
        return rows

    out["victims"] = {"total": len(v_raw), "records": _build(v_raw, "CaseMasterID")}
    out["accused"] = {"total": len(a_raw), "records": _build(a_raw, "CaseMasterID")}
    out["complainants"] = {"total": len(c_raw), "records": _build(c_raw, "CaseMasterID")}
    out["cases_by_year"] = [
        {"year": y, "crime_type": ct, "count": c}
        for y in sorted(years) for ct, c in sorted(years[y].items())
    ]

    _store("socio_demographics", out)
    return out


def h_get_hotspots(c):
    try:
        return _h_get_hotspots(c)
    except Exception as e:
        import traceback
        logging.getLogger().error("hotspots error: %s\n%s", e, traceback.format_exc())
        return {"error": str(e)}


def _h_get_hotspots(c):
    p = c["params"]
    did = p.get("district_id", 1)
    eps = float(p.get("eps_km", 20.0))
    mc = int(p.get("min_cases", 3))
    cache_key = f"hotspots:{did}:{eps}:{mc}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached
    req = HotspotRequestDTO(district_id=did, eps_km=eps, min_cases=mc)
    res = c["handler"].hotspots.detect(req, db=c["handler"]._db_client)
    result = [{"cluster_id": c.cluster_id, "centroid_lat": c.centroid_lat,
               "centroid_lng": c.centroid_lng, "case_count": c.case_count,
               "radius_km": c.radius_km, "crime_type": c.crime_type}
              for c in res.clusters]
    _store(cache_key, result)
    return result


def h_get_network(c):
    res = c["handler"].graph_projector.build_graph(
        c["params"].get("accused_name", ""), c["params"].get("depth", 2))
    return {"nodes": [{"id": n.id, "label": n.label, "node_type": n.node_type,
                       "cases": n.cases, "risk_tier": n.risk_tier} for n in res.nodes],
            "edges": [{"id": e.id, "source": e.source, "target": e.target,
                       "weight": e.weight, "shared_cases": e.shared_cases} for e in res.edges]}


def h_get_dashboard_kpis(c):
    stats = c["handler"].stats.get_dashboard_stats(db=c["handler"]._db_client)
    return [
        {'label': 'Total FIRs', 'value': f"{stats.total_cases:,}", 'change': '+12.4%', 'icon': 'FileText'},
        {'label': 'Active Cases', 'value': f"{stats.pending_cases:,}", 'change': '-8.2%', 'icon': 'Activity'},
        {'label': 'Clearance Rate', 'value': f"{100 - stats.heinous_pct}%", 'change': '+3.1%', 'icon': 'CheckCircle'},
        {'label': 'Districts Covered', 'value': str(stats.district_count), 'change': '+0', 'icon': 'MapPin'},
    ]


def h_get_alerts(c):
    alerts = c["handler"].alerts.evaluate(c["params"].get("district_id"))
    return [{"id": a.alert_id, "severity": a.severity, "title": a.title,
             "description": a.description, "rule_id": a.rule_id,
             "trigger_condition": a.triggering_condition, "created_at": a.created_at,
             "acknowledged": False, "evidence": a.evidence} for a in alerts]


def h_acknowledge_alert(c):
    return ({"status": "acknowledged", "alert_id": c["params"].get("alert_id", "")}, 200)


def h_import_table(c):
    table_name = c["params"].get("table_name", "")
    rows = c["params"].get("rows", [])
    if not table_name or not rows:
        return ({"error": "INVALID_PARAMS", "message": "table_name and rows required"}, 400)
    if c["user_context"]:
        scope = c["handler"].rbac.row_filter_clause(c["user_context"])
        if scope:
            logging.getLogger().info("RBAC scope applied to import_table: %s", scope)
    return c["handler"]._db_client.insert_bulk_rows(table_name, rows)


def h_run_sql(c):
    p = c["params"]
    sql = p.get("sql", "")
    if not sql:
        return ({"error": "sql required"}, 400)
    if c["user_context"]:
        scope = c["handler"].rbac.row_filter_clause(c["user_context"])
        if scope and sql.strip().upper().startswith("SELECT"):
            if "WHERE" in sql.upper():
                sql = sql.replace("WHERE ", f"WHERE {scope} AND ", 1)
            else:
                idx = sql.upper().rfind("LIMIT")
                if idx > 0:
                    sql = sql[:idx] + f" WHERE {scope} " + sql[idx:]
                else:
                    sql += f" WHERE {scope}"
    return c["handler"]._db_client.execute_non_query(sql)


def h_describe_table(c):
    app = c["handler"]._catalyst_app
    if not app:
        return ({"error": "SDK_NOT_INITIALIZED"}, 500)
    tbl = app.datastore().table(c["params"].get("table_name", ""))
    names = []
    for col in tbl.get_all_columns():
        d = col.to_dict() if hasattr(col, "to_dict") else col
        names.append(d.get("column_name", ""))
    return {"columns": names}


def _voice_module():
    from common.voice.voice_handler import VoiceHandler
    return VoiceHandler()


def h_speech_to_text(c):
    audio_bytes = bytes(c["params"].get("audio_bytes", []))
    language = c["params"].get("language", "en")
    text = _voice_module().speech_to_text(audio_bytes, language)
    return {"text": text}


def h_text_to_speech(c):
    text = c["params"].get("text", "")
    language = c["params"].get("language", "en")
    audio_bytes = _voice_module().text_to_speech(text, language)
    return {"audio_bytes": list(audio_bytes)}


def h_list_audit_log(c):
    p = c["params"]
    return c["handler"].audit.get_recent(
        p.get("limit", 100), p.get("event_type"), p.get("category"), p.get("actor"))


def h_commander_query(c):
    return c["handler"].commander.run(c["params"].get("query", ""), c["user_context"])


def h_create_investigation(c):
    inv = c["handler"].investigations.create(
        c["params"].get("title", ""), c["params"].get("description", ""),
        c["user_context"].user_id)
    return inv.model_dump()


def h_list_investigations(c):
    return c["handler"].investigations.list_all()


def h_get_investigation(c):
    result = c["handler"].investigations.get(c["params"].get("investigation_id", ""))
    if not result:
        return ({"error": "NOT_FOUND"}, 404)
    return result


def h_add_case_to_investigation(c):
    ok = c["handler"].investigations.add_case(
        c["params"].get("investigation_id", ""), c["params"].get("case_master_id", 0),
        c["params"].get("notes", ""))
    if not ok:
        return ({"error": "NOT_FOUND"}, 404)
    return {"status": "ok"}


def h_add_graph_to_investigation(c):
    saved = c["handler"].investigations.add_graph(
        c["params"].get("investigation_id", ""), c["params"].get("graph_data", {}),
        c["params"].get("label", ""))
    if not saved:
        return ({"error": "NOT_FOUND"}, 404)
    return saved.model_dump()


def h_get_case_similarity(c):
    return [s.model_dump() for s in c["handler"].similarity.find_similar(
        c["params"].get("case_master_id", 0), c["params"].get("top_k", 5))]


def h_get_case_timeline(c):
    return [t.model_dump() for t in c["handler"].timeline.generate(
        c["params"].get("case_master_id", 0))]


def h_get_case_leads(c):
    return [lead.model_dump() for lead in c["handler"].leads.generate_leads(
        c["params"].get("case_master_id", 0))]


def h_generate_investigation_report(c):
    inv_data = c["handler"].investigations.get(c["params"].get("investigation_id", ""))
    if not inv_data:
        return ({"error": "NOT_FOUND"}, 404)
    report = c["handler"].inv_reports.generate(c["params"]["investigation_id"], inv_data)
    resp = report.model_dump()
    url = report.stratus_url or ""
    bucket = resp.get("created_at", "").split("|", 1)[1] if "|" in resp.get("created_at", "") else None
    resp["file_id"] = url.split("/")[-1] if url else ""
    resp["url"] = url
    resp["bucket"] = bucket
    return resp


def h_list_models(c):
    return [m.model_dump() for m in c["handler"].model_registry.list_all()]


def h_register_model(c):
    p = c["params"]
    entry = c["handler"].model_registry.register(
        p.get("model_name", ""), p.get("model_version", ""), p.get("provider", ""),
        p.get("capabilities"), p.get("parameters"))
    return entry.model_dump()


def h_list_prompts(c):
    return [p.model_dump() for p in c["handler"].prompt_registry.list_all()]


def h_register_prompt(c):
    p = c["params"]
    entry = c["handler"].prompt_registry.register(
        p.get("prompt_name", ""), p.get("prompt_version", ""),
        p.get("prompt_text", ""), p.get("model_id"))
    return entry.model_dump()


def h_list_agent_capabilities(c):
    return [a.model_dump() for a in c["handler"].agent_capabilities.list_all()]


def h_list_executions(c):
    mission_id = c["params"].get("mission_id", "")
    if mission_id:
        return [e.model_dump() for e in c["handler"].execution_tracker.list_by_mission(mission_id)]
    return ({"error": "mission_id required"}, 400)


def h_list_missions(c):
    return [m.model_dump() for m in c["handler"].mission_tracker.list_missions()]


def h_get_mission(c):
    mission = c["handler"].mission_tracker.get_mission(c["params"].get("mission_id", ""))
    if not mission:
        return ({"error": "NOT_FOUND"}, 404)
    tasks = c["handler"].mission_tracker.list_tasks(mission.mission_id)
    return {"mission": mission.model_dump(), "tasks": [t.model_dump() for t in tasks]}


def h_list_claims(c):
    return [c.model_dump() for c in c["handler"].claim_ledger.list_all()]


def h_add_claim(c):
    p = c["params"]
    entry = c["handler"].claim_ledger.add_entry(
        p.get("statement", ""), p.get("classification", "DATABASE_FACT"),
        p.get("producer", ""), p.get("model_version"), p.get("evidence_refs"),
        p.get("confidence", 1.0), p.get("source_execution_id"))
    return entry.model_dump()


def h_update_claim_status(c):
    ok = c["handler"].claim_ledger.update_status(
        c["params"].get("claim_id", ""), c["params"].get("status", "Under Review"))
    if not ok:
        return ({"error": "NOT_FOUND"}, 404)
    return {"status": "ok"}


# Communication suite (delegated to short helpers written below).
def _comms(): return None  # the handler already exposes self.messages


def h_send_message(c):
    p = c["params"]
    msg = c["handler"].messages.send(
        p.get("type", "STATUS_UPDATE"), p.get("sender_id", 0),
        p.get("sender_name", ""), p.get("unit_id", 0), p.get("unit_name", ""),
        p.get("to_ids", []), p.get("subject", ""), p.get("body", ""),
        p.get("cc_ids"), p.get("linked_resources"), p.get("attachments"),
        p.get("priority", "NORMAL"), p.get("parent_message_id"),
    )
    return msg.model_dump()


def h_list_inbox(c):
    p = c["params"]
    return [m.model_dump() for m in c["handler"].messages.list_inbox(
        p.get("employee_id", 0), p.get("unread_only", False),
        p.get("priority_filter"), p.get("since"))]


def h_get_message(c):
    msg = c["handler"].messages.get(c["params"].get("message_id", ""))
    if not msg:
        return ({"error": "NOT_FOUND"}, 404)
    return msg.model_dump()


def h_mark_read(c):
    p = c["params"]
    mid = p.get("message_id", "")
    ok = c["handler"].messages.mark_read(mid, p.get("employee_id", 0))
    return {"ok": ok}


def h_acknowledge_message(c):
    p = c["params"]
    mid = p.get("message_id", "")
    ok = c["handler"].messages.acknowledge(mid, p.get("employee_id", 0))
    return {"ok": ok}


def h_get_thread(c):
    return [m.model_dump() for m in c["handler"].messages.get_thread(
        c["params"].get("message_id", ""))]


def h_list_all_messages(c):
    return [m.model_dump() for m in c["handler"].messages.list_all()]


def h_check_permission(c):
    p = c["params"]
    result = c["handler"].permissions.check(
        p.get("rank", ""), p.get("resource_type", ""), p.get("action", ""),
        p.get("scope", "own_station"))
    return result.model_dump()


def h_get_effective_permissions(c):
    p = c["params"]
    return c["handler"].permissions.get_effective(p.get("rank", ""), p.get("resource_type", ""))


def h_delegate_permission(c):
    p = c["params"]
    entry = c["handler"].permissions.delegate(
        p.get("grantor_id", 0), p.get("grantee_id", 0), p.get("permission", ""),
        p.get("scope", "own_station"), p.get("valid_until"), p.get("reason", ""))
    return entry.model_dump()


def h_revoke_delegation(c):
    pid = c["params"].get("permission_id", "")
    ok = c["handler"].permissions.revoke_delegation(pid)
    return {"ok": ok}


def h_list_delegations(c):
    p = c["params"]
    return [d.model_dump() for d in c["handler"].permissions.list_delegations(
        p.get("grantor_id"), p.get("grantee_id"))]


def h_set_emergency(c):
    p = c["params"]
    c["handler"].permissions.set_emergency(p.get("active", False), p.get("duration_hours", 72))
    return {"status": "ok", "emergency": c["handler"].permissions.is_emergency}


def h_get_emergency_status(c):
    return {"emergency": c["handler"].permissions.is_emergency}


def h_create_org_group(c):
    p = c["params"]
    g = c["handler"].groups.create_org_group(
        p.get("name", ""), p.get("group_type", "STATION"), p.get("parent_id"))
    return g.model_dump()


def h_list_org_groups(c):
    return [g.model_dump() for g in c["handler"].groups.list_org_groups(
        c["params"].get("group_type"))]


def h_create_dynamic_group(c):
    p = c["params"]
    dissolve_h = p.get("dissolve_hours")
    duration_days = dissolve_h / 24 if dissolve_h else p.get("duration_days", 90)
    g = c["handler"].groups.create_dynamic_group(
        p.get("name", ""), p.get("group_type", "TASK_FORCE"), p.get("lead_id", 0),
        p.get("case_ids"), p.get("offender_ids"), duration_days, p.get("description"))
    return g.model_dump()


def h_list_dynamic_groups(c):
    return [g.model_dump() for g in c["handler"].groups.list_dynamic_groups(
        c["params"].get("active_only", True))]


def h_dissolve_group(c):
    gid = c["params"].get("group_id", "")
    ok = c["handler"].groups.dissolve_group(gid)
    return {"ok": ok}


def h_add_group_member(c):
    p = c["params"]
    m = c["handler"].groups.add_group_member(
        p.get("group_id", ""), p.get("employee_id", 0),
        p.get("role_in_group") or p.get("role", "MEMBER"), p.get("can_modify", False),
        p.get("can_approve", False), p.get("data_scope", "group"))
    if not m:
        return ({"error": "NOT_FOUND"}, 404)
    return m.model_dump()


def h_remove_group_member(c):
    p = c["params"]
    ok = c["handler"].groups.remove_group_member(p.get("group_id", ""), p.get("employee_id", 0))
    return {"ok": ok}


def h_list_group_members(c):
    return [m.model_dump() for m in c["handler"].groups.list_members(
        c["params"].get("group_id", ""))]


def h_list_my_groups(c):
    return [g.model_dump() for g in c["handler"].groups.list_groups_for_employee(
        c["params"].get("employee_id", 0))]


def h_create_coordination(c):
    p = c["params"]
    req = c["handler"].groups.create_coordination(
        p.get("from_id", 0), p.get("to_unit_id", 0),
        p.get("request_type", "SUSPECT_LOCATION"), p.get("subject", ""),
        p.get("body", ""), p.get("case_id"))
    return req.model_dump()


def h_update_coordination(c):
    p = c["params"]
    ok = c["handler"].groups.update_coordination(
        p.get("request_id", ""), p.get("status", ""), p.get("assigned_to"))
    return {"ok": ok}


def h_list_coordination(c):
    p = c["params"]
    return [r.model_dump() for r in c["handler"].groups.list_coordination(
        p.get("from_id"), p.get("to_unit"), p.get("status"))]


def h_tse_schema_tables(c): return c["handler"].tse.schema_tables()


def h_tse_schema_columns(c):
    tbl = c["params"].get("table_name", "")
    if not tbl:
        return ({"error": "table_name required"}, 400)
    if c["user_context"] and not c["handler"].rbac.table_access_allowed(
            c["user_context"].role_name, tbl):
        return ({"error": "TABLE_DENIED",
                 "message": f"Table '{tbl}' is denied for role '{c['user_context'].role_name}'."},
                403)
    return c["handler"].tse.schema_columns(tbl)


def h_tse_constraint_check(c): return c["handler"].tse.constraint_check()
def h_tse_system_metrics(c): return c["handler"].tse.system_metrics()
def h_tse_active_sessions(c): return c["handler"].tse.active_sessions()
def h_tse_index_stats(c): return c["handler"].tse.index_stats()


def h_tse_error_logs(c):
    return c["handler"].tse.error_logs(c["params"].get("limit", 20))


def h_tse_cache_stats(c): return c["handler"].tse.cache_stats()
def h_tse_auth_tokens(c): return c["handler"].tse.auth_tokens()


def h_tse_validate_sql(c):
    sql = c["params"].get("sql", "")
    if not sql:
        return ({"error": "sql required"}, 400)
    return c["handler"].tse.validate_sql(sql)


def h_debug_analytics(c):
    from common.db.datastore_client import DatastoreClient
    db = DatastoreClient(c["handler"]._catalyst_app)
    return {"connected": db.is_connected, "msg": "ok"}


def h_run_analytics(c):
    """Run all 4 precompute phases: trends, hotspots, forecast, entity_resolution."""
    app = c["handler"]._catalyst_app
    results = {}
    phases = [
        ("trends", lambda: c["handler"].trends.compute_all_and_store(app)),
        ("hotspots", lambda: c["handler"].hotspots.compute_all_and_store(app)),
        ("forecast", lambda: c["handler"].forecaster.compute_all_and_store(app)),
        ("entity_resolution", lambda: c["handler"].resolver.compute_all_and_store(app)),
    ]
    for name, fn in phases:
        try:
            out = fn()
            results[name] = ("ok", out)
        except Exception as e:
            results[name] = ("error", str(e))
            logging.getLogger(__name__).error("analytics phase %s failed: %s", name, e)
    return results


def register_actions(handler):
    """Returns a mapping action-name → callable.

    Each callable takes the result of :func:`_ctx` and returns either a
    bare payload (HTTP 200) or a ``(payload, status_code)`` tuple. The
    thin controller in ``main.py`` wraps every tuple into a Flask
    response. New actions register here, never inside ``main.py``.
    """
    actions = {
        "login": h_login, "verify_token": h_verify_token,
        "chat_query": h_chat_query,
        "get_crime_stats": h_get_crime_stats,
        "get_forecast": h_get_forecast,
        "get_offender_profile": h_get_offender_profile,
        "create_offender_profile": h_create_offender_profile,
        "get_trends": h_get_trends,
        "get_hotspots": h_get_hotspots,
        "get_network": h_get_network,
        "get_dashboard_kpis": h_get_dashboard_kpis,
        "get_alerts": h_get_alerts,
        "acknowledge_alert": h_acknowledge_alert,
        "import_table": h_import_table,
        "run_sql": h_run_sql,
        "describe_table": h_describe_table,
        "speech_to_text": h_speech_to_text,
        "text_to_speech": h_text_to_speech,
        "list_audit_log": h_list_audit_log,
        "commander_query": h_commander_query,
        "create_investigation": h_create_investigation,
        "list_investigations": h_list_investigations,
        "get_investigation": h_get_investigation,
        "add_case_to_investigation": h_add_case_to_investigation,
        "add_graph_to_investigation": h_add_graph_to_investigation,
        "get_case_similarity": h_get_case_similarity,
        "get_case_timeline": h_get_case_timeline,
        "get_case_leads": h_get_case_leads,
        "generate_investigation_report": h_generate_investigation_report,
        "list_models": h_list_models,
        "register_model": h_register_model,
        "list_prompts": h_list_prompts,
        "register_prompt": h_register_prompt,
        "list_agent_capabilities": h_list_agent_capabilities,
        "list_executions": h_list_executions,
        "list_missions": h_list_missions,
        "get_mission": h_get_mission,
        "list_claims": h_list_claims,
        "add_claim": h_add_claim,
        "update_claim_status": h_update_claim_status,
        "send_message": h_send_message,
        "list_inbox": h_list_inbox,
        "get_message": h_get_message,
        "mark_read": h_mark_read,
        "acknowledge_message": h_acknowledge_message,
        "get_thread": h_get_thread,
        "list_all_messages": h_list_all_messages,
        "check_permission": h_check_permission,
        "get_effective_permissions": h_get_effective_permissions,
        "delegate_permission": h_delegate_permission,
        "revoke_delegation": h_revoke_delegation,
        "list_delegations": h_list_delegations,
        "set_emergency": h_set_emergency,
        "get_emergency_status": h_get_emergency_status,
        "create_org_group": h_create_org_group,
        "list_org_groups": h_list_org_groups,
        "create_dynamic_group": h_create_dynamic_group,
        "list_dynamic_groups": h_list_dynamic_groups,
        "dissolve_group": h_dissolve_group,
        "add_group_member": h_add_group_member,
        "remove_group_member": h_remove_group_member,
        "list_group_members": h_list_group_members,
        "list_my_groups": h_list_my_groups,
        "create_coordination": h_create_coordination,
        "update_coordination": h_update_coordination,
        "list_coordination": h_list_coordination,
        "tse_schema_tables": h_tse_schema_tables,
        "tse_schema_columns": h_tse_schema_columns,
        "tse_constraint_check": h_tse_constraint_check,
        "tse_system_metrics": h_tse_system_metrics,
        "tse_active_sessions": h_tse_active_sessions,
        "tse_index_stats": h_tse_index_stats,
        "tse_error_logs": h_tse_error_logs,
        "tse_cache_stats": h_tse_cache_stats,
        "tse_auth_tokens": h_tse_auth_tokens,
        "tse_validate_sql": h_tse_validate_sql,
        "debug_analytics": h_debug_analytics,
        "run_analytics": h_run_analytics,
        "get_socio_demographics": h_get_socio_demographics,
    }

    def _wrap(name, fn):
        def runner(ctx):
            res = fn(ctx)
            if isinstance(res, tuple) and len(res) == 2:
                return res[0], res[1], name
            return res, 200, name
        return runner

    return {name: _wrap(name, fn) for name, fn in actions.items()}
