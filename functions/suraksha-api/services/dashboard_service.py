from sqlalchemy.orm import Session
from models.datastore_models import CaseMaster, CaseStatusMaster, Alert
from typing import Dict, Any


class DashboardService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._case_model = CaseMaster()
        self._alert_model = Alert()

    def get_summary_metrics(self) -> Dict[str, Any]:
        cases = self._case_model.get_all() or []
        alerts = self._alert_model.get_all() or []

        total = len(cases)
        open_cases = sum(1 for c in cases if c.get("CaseStatusID") in ("1", "4", "6"))
        active_alerts = sum(1 for a in alerts if a.get("Status", "").lower() == "active")

        return {
            "total_cases": total,
            "total_open_cases": open_cases,
            "active_investigations": open_cases,
            "unread_alerts_count": active_alerts,
            "total_alerts": len(alerts),
            "forecast_trends": "rising" if total > 30 else "normal"
        }
