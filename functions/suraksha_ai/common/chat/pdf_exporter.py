import uuid
from common.models.dto import ReportJobDTO
from datetime import datetime


class PDFExporter:
    def export_conversation(self, conversation_id: str) -> ReportJobDTO:
        job = ReportJobDTO(
            job_id=str(uuid.uuid4()), status="completed",
            stratus_url=f"/exports/conversation_{conversation_id}.pdf",
            created_at=datetime.now().isoformat()
        )
        return job

    def export_investigation(self, investigation_id: str) -> ReportJobDTO:
        job = ReportJobDTO(
            job_id=str(uuid.uuid4()), status="completed",
            stratus_url=f"/exports/investigation_{investigation_id}.pdf",
            created_at=datetime.now().isoformat()
        )
        return job
