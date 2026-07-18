"""Default implementations of the narrow security interfaces (Part E.4)."""
from __future__ import annotations

import fnmatch
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from models.dto import UserContextDTO, AuditLogEntryDTO

logger = logging.getLogger(__name__)

CASE_DATA_TABLES = frozenset({
    "CaseMaster", "Accused", "ComplainantDetails", "Victim",
    "ArrestSurrender", "ChargesheetDetails", "ActSectionAssociation",
    "CrimeHeadActSection", "Employee",
})

ROLE_PERMISSIONS = {
    "Investigator": {
        "actions": ["chat_query", "view_offender", "view_network", "export_pdf",
                    "manage_investigation", "file_fir", "manage_chargesheet",
                    "create_investigation", "list_investigations", "get_investigation",
                    "add_case_to_investigation", "add_graph_to_investigation",
                    "get_case_similarity", "get_case_timeline", "get_case_leads",
                    "generate_investigation_report",
                    "list_models", "list_prompts", "list_agent_capabilities",
                    "list_missions", "get_mission", "list_claims", "add_claim",
                    "update_claim_status", "list_executions",
                    "send_message", "list_inbox", "get_message", "mark_read",
                    "acknowledge_message", "get_thread",
                    "check_permission", "get_effective_permissions",
                    "list_my_groups", "list_dynamic_groups",
                    "create_coordination", "list_coordination", "list_audit_log"],
        "scope": "unit", "max_rows": 5000, "denied_tables": [],
        "pii_visible": True, "column_mask": [],
    },
    "Analyst": {
        "actions": ["view_trends", "view_forecast", "export_pdf", "chat_query",
                    "view_command_center", "view_similarity", "view_geospatial",
                    "get_case_similarity", "get_case_timeline", "get_case_leads",
                    "list_claims",
                    "list_inbox", "get_message", "mark_read", "get_thread",
                    "check_permission", "get_effective_permissions",
                    "list_my_groups", "list_audit_log"],
        "scope": "district", "max_rows": 10000, "denied_tables": [],
        "pii_visible": False, "column_mask": ["AccusedName", "VictimName", "ComplainantName"],
    },
    "Supervisor": {
        "actions": ["chat_query", "view_offender", "view_network", "view_trends",
                    "view_forecast", "export_pdf", "manage_investigation", "file_fir",
                    "manage_chargesheet", "view_command_center", "view_similarity", "view_geospatial",
                    "create_investigation", "list_investigations", "get_investigation",
                    "add_case_to_investigation", "add_graph_to_investigation",
                    "get_case_similarity", "get_case_timeline", "get_case_leads",
                    "generate_investigation_report",
                    "list_models", "list_prompts", "list_agent_capabilities",
                    "list_missions", "get_mission", "list_claims", "add_claim",
                    "update_claim_status", "list_executions",
                    "send_message", "list_inbox", "get_message", "mark_read",
                    "acknowledge_message", "get_thread", "list_all_messages",
                    "check_permission", "get_effective_permissions",
                    "delegate_permission", "revoke_delegation", "list_delegations",
                    "create_org_group", "list_org_groups",
                    "create_dynamic_group", "list_dynamic_groups", "dissolve_group",
                    "add_group_member", "remove_group_member", "list_group_members",
                    "list_my_groups",
                    "create_coordination", "update_coordination", "list_coordination",
                    "list_audit_log"],
        "scope": "district", "max_rows": 10000, "denied_tables": [],
        "pii_visible": True, "column_mask": [],
    },
    "Policymaker": {
        "actions": ["view_trends", "view_forecast", "export_pdf"],
        "scope": "state", "max_rows": 50000, "denied_tables": [],
        "pii_visible": False, "column_mask": ["*"],
    },
    "System Administrator": {
        "actions": ["*"],
        "scope": "state", "max_rows": 100000, "denied_tables": [],
        "pii_visible": True, "column_mask": [],
    },
    "Technical Support Engineer": {
        "actions": ["tse_*", "list_audit_log", "check_permission", "get_effective_permissions"],
        "scope": "state", "max_rows": 100, "denied_tables": sorted(CASE_DATA_TABLES),
        "pii_visible": False, "column_mask": ["*"],
    },
}

_PERMISSION_OVERRIDES: dict[str, dict] = {}


def load_role_overrides_from_db(db) -> None:
    """Mutates the module-level dict with rows from RolePermissions. Failure is silent."""
    if db is None or not getattr(db, "is_connected", False):
        return
    try:
        res = db.execute_non_query("SELECT * FROM RolePermissions")
        if "rows" not in res or not res["rows"]:
            return
        for row in res["rows"]:
            d = dict(zip(res.get("columns", []), row))
            role = d.get("role_name", "")
            if not role:
                continue
            merged = dict(ROLE_PERMISSIONS.get(role, {}))
            try:
                merged["actions"] = json.loads(d.get("allowed_actions_json", "[]"))
            except (TypeError, ValueError):
                pass
            if d.get("data_scope"):
                merged["scope"] = d["data_scope"]
            try:
                merged["max_rows"] = int(d.get("max_rows", merged.get("max_rows", 5000)))
            except (TypeError, ValueError):
                pass
            try:
                merged["denied_tables"] = json.loads(d.get("denied_tables_json", "[]"))
            except (TypeError, ValueError):
                pass
            merged["pii_visible"] = str(d.get("pii_visible", "false")).lower() == "true"
            try:
                merged["column_mask"] = json.loads(d.get("column_mask_json", "[]"))
            except (TypeError, ValueError):
                pass
            _PERMISSION_OVERRIDES[role] = merged
        logger.info("Loaded %d role overrides from Data Store", len(_PERMISSION_OVERRIDES))
    except Exception as e:
        logger.warning("Role-permission override load failed; using static defaults: %s", e)


def _perms_for(role_name: str) -> dict:
    return (_PERMISSION_OVERRIDES.get(role_name)
            or ROLE_PERMISSIONS.get(role_name)
            or ROLE_PERMISSIONS["Investigator"])


class DefaultPermissionChecker:
    """Narrow: authorize an action for a user/role (Part E.4)."""

    def can_access(self, user_role: str, action: str, scope: Optional[dict] = None) -> bool:
        perms = _perms_for(user_role)
        if perms.get("actions") == ["*"]:
            return True
        if action in perms.get("actions", []):
            return True
        return any(fnmatch.fnmatch(action, p) for p in perms.get("actions", []))


class DefaultRowScopeProvider:
    """Narrow: emit row-scope WHERE clause / max-rows / table allowlist."""

    def row_filter_clause(self, user: UserContextDTO) -> str:
        perms = _perms_for(user.role_name)
        if perms.get("scope") == "state":
            return ""
        if perms.get("scope") == "district" and user.district_id:
            return f"DistrictID = {user.district_id}"
        if perms.get("scope") == "unit" and user.unit_id:
            return f"PoliceStationID = {user.unit_id}"
        return f"DistrictID = {user.district_id or 18}"

    def max_rows(self, user_role: str) -> int:
        return int(_perms_for(user_role).get("max_rows", 5000))

    def is_table_allowed(self, user_role: str, table_name: str) -> bool:
        denied = _perms_for(user_role).get("denied_tables", []) or []
        return table_name not in denied


class DefaultPIIMasker:
    """Narrow: redact PII per role (Part E.4)."""

    def mask(self, row_data: dict, user_role: str) -> dict:
        perms = _perms_for(user_role)
        if perms.get("pii_visible"):
            return row_data
        masked = dict(row_data)
        for col in perms.get("column_mask", []) or []:
            if col == "*":
                for key in list(masked):
                    if re.search(r"(Name|Aadhar|Phone|Email)", key, re.I):
                        masked[key] = "*** MASKED ***"
                break
            if col in masked:
                masked[col] = "*** MASKED ***"
        return masked


class DefaultAuditLogger:
    """Narrow: append-only audit log (Part E.4). Persists to ``AuditLog`` table when live."""

    def __init__(self, db=None):
        self._db = db
        self._entries: list[AuditLogEntryDTO] = []
        self._table = "AuditLog"

    def _is_live(self) -> bool:
        return self._db is not None and getattr(self._db, "is_connected", False)

    def log(self, user: Optional[UserContextDTO], action: str, params: dict, result: str) -> None:
        params = params or {}
        entry = AuditLogEntryDTO(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=action,
            category=self._categorize(action),
            actor_kgid=user.kgid if user else "system",
            actor_role=user.role_name if user else "system",
            resource_type=params.get("resource_type", params.get("table", "")),
            resource_id=str(_nested_get(params, "resource_id", "message_id", "permission_id",
                                         "group_id", "request_id", "alert_id", "claim_id",
                                         "model_id", "prompt_id")),
            detail=params.get("detail", params.get("reason", action)),
            result=result,
        )
        self._entries.append(entry)
        if self._is_live():
            try:
                self._db.insert_bulk_rows(
                    self._table,
                    [{k: (v if not isinstance(v, bool) else str(v).lower())
                      for k, v in entry.model_dump().items()}]
                )
            except Exception as e:
                logger.warning("Audit log DB insert failed: %s", e)
        logger.info("AUDIT: user=%s action=%s result=%s",
                    user.kgid if user else "system", action, result)

    def recent(self, limit: int = 100, event_type: Optional[str] = None,
               category: Optional[str] = None, actor: Optional[str] = None) -> list:
        if self._is_live():
            try:
                res = self._db.execute_non_query(
                    f"SELECT * FROM {self._table} ORDER BY timestamp DESC"
                )
                if res.get("rows"):
                    for row in res["rows"]:
                        d = dict(zip(res.get("columns", []), row))
                        try:
                            entry = AuditLogEntryDTO(**d)
                        except Exception:
                            continue
                        if not any(e.entry_id == entry.entry_id for e in self._entries):
                            self._entries.append(entry)
            except Exception as e:
                logger.warning("Audit log DB load failed: %s", e)
        result = list(reversed(self._entries))
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        if category:
            result = [e for e in result if e.category == category]
        if actor:
            lo = actor.lower()
            result = [e for e in result if lo in e.actor_kgid.lower() or lo in e.actor_role.lower()]
        return [e.model_dump() for e in result[:limit]]

    @staticmethod
    def _categorize(action: str) -> str:
        if action.startswith(("send_", "list_", "get_", "mark_")) or action == "acknowledge_message":
            return "communication"
        if "permission" in action or "delegate" in action or "emergency" in action \
                or action in ("check_permission", "revoke_delegation"):
            return "access_control"
        if "group" in action or "member" in action:
            return "group_management"
        if "coordination" in action:
            return "coordination"
        if action in ("login", "verify_token"):
            return "authentication"
        return "system"


def _nested_get(d: dict, *keys: str) -> str:
    for k in keys:
        v = d.get(k)
        if v:
            return str(v)
    return ""
