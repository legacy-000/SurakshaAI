import json, uuid
from datetime import datetime, timedelta
from typing import Optional
from models.dto import PermissionCheckDTO, TempPermissionDTO

PERMISSION_MATRIX = {
    "Constable": {
        "CASE": {"CREATE": True, "READ": "own_station", "UPDATE": False, "APPROVE": False, "DELETE": False, "EXPORT": "own_station"},
        "ARREST": {"CREATE": False, "READ": "own_station", "UPDATE_BAIL": False, "UPDATE_CUSTODY": False},
        "CHARGESHEET": {"CREATE": False, "READ": "own_station", "UPDATE": False, "APPROVE": False},
        "MESSAGE": {"SEND_UP": True, "SEND_LATERAL": False, "SEND_DOWN": False, "BROADCAST": False},
        "OFFENDER": {"READ": "own_station", "ADD_NOTE": False, "UPDATE_PRIORITY": False},
    },
    "Sub-Inspector": {
        "CASE": {"CREATE": "own_station", "READ": "assigned", "UPDATE": "assigned", "APPROVE": False, "DELETE": False, "EXPORT": "assigned"},
        "ARREST": {"CREATE": "own_case", "READ": "assigned", "UPDATE_BAIL": "own_case", "UPDATE_CUSTODY": False},
        "CHARGESHEET": {"CREATE": "own_case", "READ": "assigned", "UPDATE": "own_case", "APPROVE": False},
        "MESSAGE": {"SEND_UP": True, "SEND_LATERAL": True, "SEND_DOWN": False, "BROADCAST": False},
        "OFFENDER": {"READ": "own_district", "ADD_NOTE": "own_case", "UPDATE_PRIORITY": False},
    },
    "SHO": {
        "CASE": {"CREATE": "all", "READ": "own_station", "UPDATE": "own_station", "APPROVE": "own_station", "DELETE": False, "EXPORT": "own_station"},
        "ARREST": {"CREATE": "own_station", "READ": "own_station", "UPDATE_BAIL": "own_station", "UPDATE_CUSTODY": "own_station"},
        "CHARGESHEET": {"CREATE": False, "READ": "own_station", "UPDATE": False, "APPROVE": "own_station"},
        "MESSAGE": {"SEND_UP": True, "SEND_LATERAL": True, "SEND_DOWN": True, "BROADCAST": "own_station"},
        "OFFENDER": {"READ": "own_district", "ADD_NOTE": "own_station", "UPDATE_PRIORITY": False},
    },
    "DSP": {
        "CASE": {"CREATE": "all", "READ": "own_district", "UPDATE": "own_district", "APPROVE": "own_district", "DELETE": False, "EXPORT": "own_district"},
        "ARREST": {"CREATE": "all", "READ": "own_district", "UPDATE_BAIL": "own_district", "UPDATE_CUSTODY": "own_district"},
        "CHARGESHEET": {"CREATE": False, "READ": "own_district", "UPDATE": False, "APPROVE": "own_district"},
        "MESSAGE": {"SEND_UP": True, "SEND_LATERAL": True, "SEND_DOWN": True, "BROADCAST": "own_district"},
        "OFFENDER": {"READ": "all", "ADD_NOTE": "own_district", "UPDATE_PRIORITY": "own_district"},
    },
    "Commissioner": {
        "CASE": {"CREATE": "all", "READ": "all", "UPDATE": "all", "APPROVE": "all", "DELETE": False, "EXPORT": "all"},
        "ARREST": {"CREATE": "all", "READ": "all", "UPDATE_BAIL": "all", "UPDATE_CUSTODY": "all"},
        "CHARGESHEET": {"CREATE": False, "READ": "all", "UPDATE": False, "APPROVE": "all"},
        "MESSAGE": {"SEND_UP": False, "SEND_LATERAL": False, "SEND_DOWN": True, "BROADCAST": "all"},
        "OFFENDER": {"READ": "all", "ADD_NOTE": "all", "UPDATE_PRIORITY": "all"},
    },
}

SCOPE_HIERARCHY = {"assigned": 0, "own_case": 1, "own_station": 2, "own_district": 3, "all": 4}


class PermissionEngine:
    def __init__(self, db=None):
        self._db = db
        self._delegations = {}
        self._emergency_mode = False
        self._emergency_until = None
        self._del_table = "PermissionDelegations"

    def _is_live(self):
        return self._db and self._db.is_connected

    def _load_delegations(self):
        if not self._is_live():
            return
        res = self._db.execute_non_query(f"SELECT * FROM {self._del_table} WHERE status='active'")
        if res.get("rows"):
            for row in res["rows"]:
                d = dict(zip(res["columns"], row))
                self._delegations[d["permission_id"]] = TempPermissionDTO(**d)

    def check(self, rank: str, resource_type: str, action: str, scope: str = None) -> PermissionCheckDTO:
        allowed = False
        reason = ""
        if self._emergency_mode:
            allowed = True
            reason = "Emergency mode — permissions suspended"
        else:
            rank_perms = PERMISSION_MATRIX.get(rank, {})
            resource_perms = rank_perms.get(resource_type, {})
            required = resource_perms.get(action, False)
            if required is True:
                allowed = True
            elif required is False:
                allowed = False
                reason = f"{rank} cannot {action} {resource_type}"
            elif isinstance(required, str) and scope:
                allowed = SCOPE_HIERARCHY.get(scope, -1) <= SCOPE_HIERARCHY.get(required, -1)
                if not allowed:
                    reason = f"Scope {scope} insufficient, need {required}"
            else:
                allowed = bool(required)
        return PermissionCheckDTO(resource_type=resource_type, action=action, allowed=allowed, denial_reason=reason)

    def get_effective(self, rank: str, resource_type: str) -> list[str]:
        rank_perms = PERMISSION_MATRIX.get(rank, {})
        resource_perms = rank_perms.get(resource_type, {})
        return [a for a, v in resource_perms.items() if v]

    def delegate(self, grantor_id: int, grantee_id: int, permission: str,
                 scope: str = "own_station", valid_until: str = None,
                 reason: str = "") -> TempPermissionDTO:
        entry = TempPermissionDTO(
            permission_id=str(uuid.uuid4()),
            grantor_employee_id=grantor_id, grantee_employee_id=grantee_id,
            permission=permission, scope=scope,
            valid_from=datetime.now().isoformat(),
            valid_until=valid_until or (datetime.now() + timedelta(days=7)).isoformat(),
            reason=reason, status="active",
        )
        if self._is_live():
            self._db.insert_bulk_rows(self._del_table, [{k: (v if not isinstance(v, bool) else str(v).lower()) for k, v in entry.model_dump().items()}])
        self._delegations[entry.permission_id] = entry
        return entry

    def revoke_delegation(self, permission_id: str) -> bool:
        entry = self._delegations.get(permission_id)
        if not entry:
            return False
        entry.status = "revoked"
        if self._is_live():
            self._db.execute_non_query(f"UPDATE {self._del_table} SET status='revoked' WHERE permission_id='{permission_id.replace(chr(39),chr(39)+chr(39))}'")
        return True

    def has_delegation(self, employee_id: int, permission: str) -> Optional[TempPermissionDTO]:
        now = datetime.now().isoformat()
        for d in self._delegations.values():
            if d.grantee_employee_id == employee_id and d.permission == permission and d.status == "active" and d.valid_until >= now:
                return d
        return None

    def list_delegations(self, grantor_id: int = None, grantee_id: int = None) -> list[TempPermissionDTO]:
        self._load_delegations()
        results = list(self._delegations.values())
        if grantor_id:
            results = [d for d in results if d.grantor_employee_id == grantor_id]
        if grantee_id:
            results = [d for d in results if d.grantee_employee_id == grantee_id]
        return results

    def set_emergency(self, active: bool, duration_hours: int = 72):
        self._emergency_mode = active
        if active:
            self._emergency_until = (datetime.now() + timedelta(hours=duration_hours)).isoformat()
        else:
            self._emergency_until = None

    @property
    def is_emergency(self) -> bool:
        if not self._emergency_mode:
            return False
        if self._emergency_until and datetime.now().isoformat() > self._emergency_until:
            self._emergency_mode = False
            self._emergency_until = None
            return False
        return True
