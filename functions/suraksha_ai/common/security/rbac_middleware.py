import fnmatch, json, logging, re
from typing import Optional
from models.dto import UserContextDTO

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


class RBACMiddleware:
    def __init__(self, db=None):
        self._db = db
        self._table = "RolePermissions"

    def _is_live(self):
        return self._db and self._db.is_connected

    def _load_from_db(self) -> dict:
        """Load role permissions from Data Store, merge with static defaults."""
        if not self._is_live():
            return ROLE_PERMISSIONS
        merged = dict(ROLE_PERMISSIONS)
        try:
            res = self._db.execute_non_query(f"SELECT * FROM {self._table}")
            if res.get("rows"):
                for row in res["rows"]:
                    d = dict(zip(res["columns"], row))
                    role = d.get("role_name", "")
                    if role:
                        merged.setdefault(role, {"actions": [], "scope": "state", "max_rows": 5000, "denied_tables": [], "pii_visible": False, "column_mask": []})
                        merged[role]["actions"] = json.loads(d.get("allowed_actions_json", "[]"))
                        merged[role]["scope"] = d.get("data_scope", merged[role].get("scope", "state"))
                        merged[role]["max_rows"] = int(d.get("max_rows", merged[role].get("max_rows", 5000)))
                        merged[role]["denied_tables"] = json.loads(d.get("denied_tables_json", "[]"))
                        merged[role]["pii_visible"] = d.get("pii_visible", "false").lower() == "true"
                        merged[role]["column_mask"] = json.loads(d.get("column_mask_json", "[]"))
            logger.info("Loaded %d role permissions from Data Store", len(res.get("rows", [])))
        except Exception as e:
            logger.warning("Failed to load role permissions from Data Store, using static: %s", e)
        return merged

    def get_permissions(self, role_name: str) -> dict:
        perms = self._load_from_db()
        return perms.get(role_name, perms.get("Investigator", ROLE_PERMISSIONS["Investigator"]))

    def authorize_action(self, user: UserContextDTO, action: str) -> bool:
        perms = self.get_permissions(user.role_name)
        if perms["actions"] == ["*"]:
            return True
        if action in perms["actions"]:
            return True
        return any(fnmatch.fnmatch(action, p) for p in perms["actions"])

    def row_filter_clause(self, user: UserContextDTO) -> str:
        perms = self.get_permissions(user.role_name)
        if perms["scope"] == "state":
            return ""
        if perms["scope"] == "district" and user.district_id:
            return f"DistrictID = {user.district_id}"
        if perms["scope"] == "unit" and user.unit_id:
            return f"PoliceStationID = {user.unit_id}"
        return f"DistrictID = {user.district_id or 18}"

    def mask_pii(self, row_data: dict, role_name: str) -> dict:
        perms = self.get_permissions(role_name)
        if perms["pii_visible"]:
            return row_data
        masked = dict(row_data)
        for col in perms["column_mask"]:
            if col == "*":
                for key in masked:
                    if re.search(r"(Name|Aadhar|Phone|Email)", key, re.I):
                        masked[key] = "*** MASKED ***"
                break
            if col in masked:
                masked[col] = "*** MASKED ***"
        return masked

    def enforce_row_limit(self, role_name: str, query_limit: int = None) -> int:
        perms = self.get_permissions(role_name)
        if query_limit is None or query_limit > perms["max_rows"]:
            return perms["max_rows"]
        return query_limit

    def table_access_allowed(self, role_name: str, table_name: str) -> bool:
        perms = self.get_permissions(role_name)
        denied = perms.get("denied_tables", [])
        return table_name not in denied
