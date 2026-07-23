"""Request context: identifies the calling officer from headers.

This is a LOCAL prototype convenience -- the frontend sends the signed-in user's
identity via headers (X-User-*). A production build would derive this from a
verified session token. Used for PII masking, RBAC and audit logging.
"""
from __future__ import annotations

from fastapi import Request

# role -> capability matrix (single source of truth, shared with auth router)
# Full Karnataka State Police hierarchy
ROLE_MATRIX = {
    "constable": {
        "rank": "Police Constable",
        "screens": ["dashboard", "chat", "cases", "work", "alerts"],
        "can_view_pii": False, "can_view_sql": False, "can_export": False,
        "can_view_audit": False, "can_investigate": False, "scope": "station",
        "command_level": None,
    },
    "head_constable": {
        "rank": "Head Constable",
        "screens": ["dashboard", "chat", "cases", "work", "alerts"],
        "can_view_pii": False, "can_view_sql": False, "can_export": False,
        "can_view_audit": False, "can_investigate": False, "scope": "station",
        "command_level": None,
    },
    "asi": {
        "rank": "Assistant Sub-Inspector",
        "screens": ["dashboard", "chat", "cases", "work", "alerts", "network"],
        "can_view_pii": False, "can_view_sql": False, "can_export": False,
        "can_view_audit": False, "can_investigate": True, "scope": "station",
        "command_level": None,
    },
    "sub_inspector": {
        "rank": "Sub-Inspector",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial", "alerts", "victims"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": False, "can_investigate": True, "scope": "assigned",
        "command_level": None,
    },
    "pi": {
        "rank": "Police Inspector",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "alerts", "patterns", "victims", "approvals", "audit"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "station",
        "command_level": "station",
    },
    "sho": {
        "rank": "Station House Officer",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "alerts", "patterns", "victims", "approvals", "audit"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "station",
        "command_level": "station",
    },
    "ci": {
        "rank": "Circle Inspector",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "alerts", "patterns", "victims", "approvals", "socio", "audit"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "subdivision",
        "command_level": "subdivision",
    },
    "acp": {
        "rank": "Assistant Commissioner of Police",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit", "victims", "approvals"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "subdivision",
        "command_level": "subdivision",
    },
    "dsp": {
        "rank": "Dy. Superintendent of Police",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit", "victims", "approvals"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "subdivision",
        "command_level": "subdivision",
    },
    "sp": {
        "rank": "Superintendent of Police",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit", "victims", "approvals"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "district",
        "command_level": "district",
    },
    "dig": {
        "rank": "Deputy Inspector General",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit", "victims", "approvals"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "range",
        "command_level": "range",
    },
    "ig": {
        "rank": "Inspector General of Police",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit", "victims", "approvals"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "range",
        "command_level": "range",
    },
    "addl_dgp": {
        "rank": "Additional DGP",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit", "victims", "approvals"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "state",
        "command_level": "state",
    },
    "dgp": {
        "rank": "Director General of Police",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit", "victims", "approvals"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "state",
        "command_level": "state",
    },
    "analyst": {
        "rank": "Intelligence Analyst",
        "screens": ["dashboard", "chat", "patterns", "socio", "forecasting", "network", "victims"],
        "can_view_pii": False, "can_view_sql": True, "can_export": True,
        "can_view_audit": False, "can_investigate": False, "scope": "district",
        "command_level": None,
    },
}
DEFAULT_ROLE = "sub_inspector"


class Ctx:
    def __init__(self, user_id, name, role, district=None, subdivision=None, range_name=None):
        self.user_id = user_id
        self.name = name or "Unknown"
        self.role = role if role in ROLE_MATRIX else DEFAULT_ROLE
        self.caps = ROLE_MATRIX[self.role]
        self.district = district
        self.subdivision = subdivision
        self.range_name = range_name

    @property
    def can_view_pii(self) -> bool:
        return self.caps["can_view_pii"]

    @property
    def scope(self) -> str:
        return self.caps["scope"]

    @property
    def command_level(self):
        return self.caps.get("command_level")

    def district_filter(self):
        """District(s) the officer may see, or None for state-wide."""
        if self.scope == "state":
            return None
        if self.scope == "range":
            from .geo import get_range_districts
            return get_range_districts(self.range_name) if self.range_name else self.district
        return self.district  # district / subdivision / station / assigned all narrow to their district

    def districts_in_scope(self):
        """Return list of districts the officer can access."""
        if self.scope == "state":
            from .geo import KARNATAKA_DISTRICTS
            return list(KARNATAKA_DISTRICTS.keys())
        if self.scope == "range":
            from .geo import get_range_districts
            return get_range_districts(self.range_name) if self.range_name else [self.district]
        return [self.district] if self.district else []

    def districts_with_neighbors(self):
        """Return own district(s) + neighboring districts."""
        from .geo import get_neighbors
        own = self.districts_in_scope()
        neighbors = []
        for d in own:
            neighbors.extend(get_neighbors(d))
        return list(set(own + neighbors))


def get_ctx(request: Request) -> Ctx:
    return Ctx(
        request.headers.get("X-User-Id"),
        request.headers.get("X-User-Name"),
        request.headers.get("X-User-Role", DEFAULT_ROLE),
        request.headers.get("X-User-District"),
        request.headers.get("X-User-Subdivision"),
        request.headers.get("X-User-Range"),
    )


def mask_pii(value, show: bool, keep: int = 1):
    """Mask a PII string unless `show`. Keeps first `keep` chars."""
    if show or value is None:
        return value
    s = str(value)
    if not s:
        return s
    if len(s) <= keep:
        return "+" * 4
    return s[:keep] + "+" * max(4, len(s) - keep)
