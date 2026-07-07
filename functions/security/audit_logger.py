import uuid
from datetime import datetime
from models.dto import AuditEventDTO


class AuditLogger:
    def __init__(self):
        self._logs = []

    def log(self, event: AuditEventDTO):
        event.audit_id = str(uuid.uuid4())
        event.timestamp = datetime.now().isoformat()
        self._logs.append(event)

    def get_logs(self, user_id: str = None, action: str = None,
                 date_from: str = None, date_to: str = None) -> list[AuditEventDTO]:
        results = self._logs
        if user_id:
            results = [l for l in results if l.user_id == user_id]
        if action:
            results = [l for l in results if l.action == action]
        return results[-100:]
