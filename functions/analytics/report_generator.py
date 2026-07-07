import uuid
from datetime import datetime
from models.dto import ReportJobDTO


class ReportGenerator:
    def generate_investigation_report(self, investigation_id: str) -> ReportJobDTO:
        return ReportJobDTO(
            job_id=str(uuid.uuid4()), status="completed",
            stratus_url=f"/reports/investigation_{investigation_id}.pdf",
            created_at=datetime.now().isoformat()
        )
