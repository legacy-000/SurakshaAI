import json, logging, uuid
from datetime import datetime, timezone
from typing import Optional
from models.dto import UserContextDTO, AuditLogEntryDTO


def _nested_get(d: dict, *keys: str) -> str:
    for k in keys:
        v = d.get(k)
        if v:
            return str(v)
    return ""

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self, db=None):
        self._db = db
        self._entries: list[AuditLogEntryDTO] = []
        self._table = "AuditLog"

    def _is_live(self):
        return self._db and self._db.is_connected

    def log(self, user: Optional[UserContextDTO], action: str, params: dict = None, result: str = "success"):
        params = params or {}
        entry = AuditLogEntryDTO(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=action,
            category=self._categorize(action),
            actor_kgid=user.kgid if user else "system",
            actor_role=user.role_name if user else "system",
            resource_type=params.get("resource_type", params.get("table", "")),
            resource_id=str(_nested_get(params, "resource_id", "message_id", "permission_id", "group_id", "request_id", "alert_id", "claim_id", "model_id", "prompt_id")),
            detail=params.get("detail", params.get("reason", action)),
            result=result,
        )
        self._entries.append(entry)
        if self._is_live():
            try:
                self._db.insert_bulk_rows(self._table, [{k: (v if not isinstance(v, bool) else str(v).lower()) for k, v in entry.model_dump().items()}])
            except Exception as e:
                logger.warning("Audit log DB insert failed: %s", e)
        logger.info("AUDIT: user=%s action=%s result=%s", user.kgid if user else "system", action, result)

    def _categorize(self, action: str) -> str:
        if action.startswith("send_") or action.startswith("list_") or action.startswith("get_") or action.startswith("mark_") or action in ("acknowledge_message",):
            return "communication"
        if "permission" in action or "delegate" in action or "emergency" in action or action == "check_permission" or action == "revoke_delegation":
            return "access_control"
        if "group" in action or "member" in action:
            return "group_management"
        if "coordination" in action:
            return "coordination"
        if action in ("login", "verify_token"):
            return "authentication"
        return "system"

    def get_recent(self, limit: int = 50, event_type: Optional[str] = None, category: Optional[str] = None, actor: Optional[str] = None) -> list:
        if self._is_live():
            try:
                sql = f"SELECT * FROM {self._table} ORDER BY timestamp DESC"
                res = self._db.execute_non_query(sql)
                if res.get("rows"):
                    for row in res["rows"]:
                        d = dict(zip(res["columns"], row))
                        entry = AuditLogEntryDTO(**d)
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
            result = [e for e in result if actor.lower() in e.actor_kgid.lower() or actor.lower() in e.actor_role.lower()]
        return [e.model_dump() for e in result[:limit]]
