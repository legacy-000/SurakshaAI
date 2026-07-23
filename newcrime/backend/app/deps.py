"""Request context: identifies the calling officer from headers.

This is a LOCAL prototype convenience — the frontend sends the signed-in user's
identity via headers (X-User-*). A production build would derive this from a
verified session token. Used for PII masking, RBAC and audit logging.
"""
from fastapi import Request

# role -> capability matrix (single source of truth, shared with auth router)
ROLE_MATRIX = {
    "constable": {
        "rank": "Police Constable",
        "screens": ["dashboard", "chat", "cases", "work", "alerts"],
        "can_view_pii": False, "can_view_sql": False, "can_export": False,
        "can_view_audit": False, "can_investigate": False, "scope": "station",
    },
    "sub_inspector": {
        "rank": "Sub-Inspector (IO)",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial", "alerts"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": False, "can_investigate": True, "scope": "assigned",
    },
    "sho": {
        "rank": "Station House Officer",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "alerts", "patterns"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "station",
    },
    "dsp": {
        "rank": "Dy. Superintendent of Police",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "district",
    },
    "commander": {
        "rank": "Intelligence Commander",
        "screens": ["dashboard", "chat", "cases", "work", "network", "profiling", "financial",
                    "patterns", "socio", "forecasting", "alerts", "audit"],
        "can_view_pii": True, "can_view_sql": True, "can_export": True,
        "can_view_audit": True, "can_investigate": True, "scope": "state",
    },
    "analyst": {
        "rank": "Intelligence Analyst",
        "screens": ["dashboard", "chat", "patterns", "socio", "forecasting", "network"],
        "can_view_pii": False, "can_view_sql": True, "can_export": True,
        "can_view_audit": False, "can_investigate": False, "scope": "district",
    },
}
DEFAULT_ROLE = "sub_inspector"


class Ctx:
    def __init__(self, user_id, name, role, district=None):
        self.user_id = user_id
        self.name = name or "Unknown"
        self.role = role if role in ROLE_MATRIX else DEFAULT_ROLE
        self.caps = ROLE_MATRIX[self.role]
        self.district = district

    @property
    def can_view_pii(self) -> bool:
        return self.caps["can_view_pii"]

    @property
    def scope(self) -> str:
        return self.caps["scope"]

    def district_filter(self):
        """District(s) the officer may see, or None for state-wide."""
        if self.scope == "state":
            return None
        return self.district  # district / station / assigned all narrow to their district here


def get_ctx(request: Request) -> Ctx:
    return Ctx(
        request.headers.get("X-User-Id"),
        request.headers.get("X-User-Name"),
        request.headers.get("X-User-Role", DEFAULT_ROLE),
        request.headers.get("X-User-District"),
    )


def mask_pii(value, show: bool, keep: int = 1):
    """Mask a PII string unless `show`. Keeps first `keep` chars."""
    if show or value is None:
        return value
    s = str(value)
    if not s:
        return s
    if len(s) <= keep:
        return "•" * 4
    return s[:keep] + "•" * max(4, len(s) - keep)
