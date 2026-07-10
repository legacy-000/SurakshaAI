import uuid
from common.models.dto import EvidenceReferenceDTO


class EvidenceBuilder:
    def build_evidence(self, exec_result: dict) -> list[EvidenceReferenceDTO]:
        evidence = []
        row_count = exec_result.get("row_count", 0)

        if row_count > 0:
            evidence.append(EvidenceReferenceDTO(
                evidence_id=str(uuid.uuid4()),
                evidence_type="database_fact",
                source_table=exec_result.get("columns", ["unknown"])[0] if exec_result.get("columns") else "CaseMaster",
                source_record_count=row_count,
                display_label=f"{row_count} records retrieved from database"
            ))

        return evidence
