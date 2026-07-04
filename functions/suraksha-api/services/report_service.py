from sqlalchemy.orm import Session
from models.datastore_models import CaseMaster, Accused, Victim, TimelineEvent
from typing import Dict, Any
from datetime import datetime


class ReportService:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._case_model = CaseMaster()
        self._accused_model = Accused()
        self._victim_model = Victim()
        self._timeline_model = TimelineEvent()

    def compile_crime_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        case_id = report_config.get("case_id")
        cases = self._case_model.get_all() or []
        accused = self._accused_model.get_all() or []
        victims = self._victim_model.get_all() or []
        timelines = self._timeline_model.get_all() or []

        target_case = None
        if case_id:
            for c in cases:
                if c.get("CaseMasterID") == str(case_id):
                    target_case = c
                    break

        case_accused = [a for a in accused if a.get("CaseMasterID") == str(case_id)] if case_id else accused
        case_victims = [v for v in victims if v.get("CaseMasterID") == str(case_id)] if case_id else victims
        case_timeline = [t for t in timelines if t.get("CaseMasterID") == str(case_id)] if case_id else timelines

        return {
            "report_id": f"REP_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "config": report_config,
            "summary": {
                "total_cases": len(cases),
                "total_accused": len(accused),
                "total_victims": len(victims),
                "total_timeline_events": len(timelines)
            },
            "case": target_case or (cases[0] if cases else None),
            "accused": case_accused[:10],
            "victims": case_victims[:10],
            "timeline": case_timeline[:20]
        }
