import uuid
from datetime import datetime
from models.dto import ReportJobDTO


class ReportGenerator:
    def generate(self, investigation_id: str, investigation_data: dict) -> ReportJobDTO:
        return ReportJobDTO(
            job_id=str(uuid.uuid4()),
            status="completed",
            stratus_url=f"/export/report_{investigation_id[:8]}.pdf",
            created_at=datetime.now().isoformat(),
        )
