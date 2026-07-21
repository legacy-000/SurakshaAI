"""Thin Controller (Part G).

Every action handler lives in :mod:`common.main_handler`. This module does
only:

  1. initialize Catalyst SDK (gracefully),
  2. parse the request body,
  3. RBAC gate,
  4. dispatch through ``ACTIONS``,
  5. shape the Flask response — and wrap everything in try/except so an
     unhandled exception never strands the request inside Catalyst's 30-s
     ceiling (Part H checklist).

Adding new actions: register them in ``common.main_handler.register_actions``
only. This file does not need to change.
"""
import logging
import os
import sys
import traceback

from flask import Request, jsonify

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "common"))

from common.main_handler import SurakshaAIHandler, register_actions, _ctx
from common.models.dto import UserContextDTO

logger = logging.getLogger()


# Actions that need a live Catalyst connection before they can run. Anything
# outside this set is allowed to run in offline mode (returns fallback data).
_DB_REQUIRED_ACTIONS = frozenset({
    "chat_query", "get_crime_stats", "get_trends", "get_hotspots",
    "get_forecast", "get_offender_profile", "get_network",
    "get_dashboard_kpis", "get_alerts", "create_offender_profile",
    "import_table", "run_sql", "describe_table",
    "debug_analytics", "run_analytics", "get_socio_demographics",
    "tse_schema_tables", "tse_schema_columns", "tse_constraint_check",
    "tse_system_metrics", "tse_active_sessions", "tse_index_stats",
    "tse_error_logs", "tse_cache_stats", "tse_auth_tokens", "tse_validate_sql",
    "list_audit_log", "network_ai_query",
    "network_list_conversations", "network_get_conversation",
    "network_create_conversation", "network_delete_conversation",
    "list_conversations", "get_conversation", "delete_conversation",
    "upload_file",
})


# Actions exempt from the RBAC pre-flight (login obviously can't be RBAC-gated
# before the user has a role).
_RBAC_EXEMPT_ACTIONS = frozenset({"login", "run_analytics", "debug_analytics"})


def _maybe_init_app() -> object | None:
    """Catalyst SDK bootstrap. Returns the live app or None (offline mode)."""
    try:
        import zcatalyst_sdk
        return zcatalyst_sdk.initialize()
    except Exception as e:
        logger.warning("Catalyst SDK not initialized; running offline: %s", e)
        return None


def _parse_user_context(body: dict) -> UserContextDTO | None:
    session = (body.get("session") or {})
    uc = session.get("user_context") or {}
    if not uc:
        return None
    return UserContextDTO(
        user_id=uc.get("user_id", "convokraft"),
        kgid=uc.get("kgid", ""),
        first_name=uc.get("first_name", ""),
        email=uc.get("email", ""),
        role_id=uc.get("role_id", 1),
        role_name=uc.get("role_name", ""),
        unit_id=uc.get("unit_id"),
        district_id=uc.get("district_id"),
        language_preference=uc.get("language_preference", "en"),
    )


def handler(request: Request):
    """Single dispatcher. Pure controller — no business logic inline."""
    app = _maybe_init_app()
    handler_ = SurakshaAIHandler(app)
    actions = register_actions(handler_)

    body = (request.get_json(force=True, silent=True)
            or request.form.to_dict()
            or {})

    action = body.get("action", "") or ""
    if not action and request.method == "GET":
        action = "run_analytics"
    params = body.get("params", {}) or {}
    user_context = _parse_user_context(body)

    # 1. Unknown action — fail fast, never let an unhandled switch slide.
    if action not in actions:
        return jsonify({
            "error": "UNKNOWN_ACTION",
            "message": f"Action '{action}' is not supported.",
        }), 400

    # 2. RBAC authorize (skip for login — see _RBAC_EXEMPT_ACTIONS).
    if user_context and action not in _RBAC_EXEMPT_ACTIONS:
        if not handler_.rbac.authorize_action(user_context, action):
            handler_.audit.log(user_context, action, params, "denied")
            return jsonify({
                "error": "FORBIDDEN",
                "message": f"Role '{user_context.role_name}' cannot perform '{action}'.",
            }), 403

    # 3. Live DB requirement — protect offline-mode users from misleading errors.
    if action in _DB_REQUIRED_ACTIONS and not handler_.is_live:
        return jsonify({
            "error": "DB_NOT_CONNECTED",
            "message": "Zoho Catalyst connection required but unavailable.",
        }), 500

    # 4. Dispatch + try/except so every branch returns a valid response.
    try:
        payload, status, action_name = actions[action](
            _ctx(action, handler_, user_context, params, body)
        )
        if user_context:
            handler_.audit.log(user_context, action_name, _audit_params(action_name, params), "success")
        return jsonify(payload), status
    except Exception as exc:
        logger.exception("Error handling action %s: %s", action, exc)
        if user_context:
            handler_.audit.log(user_context, action, params, f"error: {exc}")
        return jsonify({
            "error": "INTERNAL_SERVER_ERROR",
            "message": str(exc),
            "trace": traceback.format_exc(limit=5),
        }), 500


def _audit_params(action: str, params: dict) -> dict:
    """Small, cheap audit payloads. Avoid logging huge blobs."""
    if not params:
        return {}
    keep_keys = {"name", "message_id", "permission_id", "group_id",
                 "request_id", "alert_id", "claim_id", "model_id",
                 "prompt_id", "investigation_id", "table_name", "detail"}
    small = {k: v for k, v in params.items() if k in keep_keys}
    if "message" in params and isinstance(params["message"], str):
        small["message_len"] = len(params["message"])
    if "sql" in params and isinstance(params["sql"], str):
        small["sql_len"] = len(params["sql"])
    return small
