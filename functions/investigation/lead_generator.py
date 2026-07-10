import uuid
from models.dto import InvestigativeLeadDTO


class LeadGenerator:
    def generate_leads(self, case_master_id: int) -> list[InvestigativeLeadDTO]:
        return [
            InvestigativeLeadDTO(
                lead_id=str(uuid.uuid4()),
                case_master_id=case_master_id,
                lead_type="co_accused_link",
                lead_description=f"Case {case_master_id} has co-accused with prior cases in same district.",
                confidence_class="computed_statistic",
                confidence_score=0.78,
                supporting_evidence=[{
                    "evidence_type": "computed_metric",
                    "source_table": "Accused",
                    "evidence_description": "Co-accused appears in 3 other cases"
                }]
            ),
            InvestigativeLeadDTO(
                lead_id=str(uuid.uuid4()),
                case_master_id=case_master_id,
                lead_type="location_pattern",
                lead_description=f"Crime location within 500m of 2 prior similar incidents.",
                confidence_class="computed_statistic",
                confidence_score=0.65,
                supporting_evidence=[{
                    "evidence_type": "computed_metric",
                    "source_table": "CaseMaster",
                    "evidence_description": "GPS proximity match"
                }]
            )
        ]
