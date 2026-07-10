from common.models.dto import CaseSummaryDTO, EvidenceReferenceDTO
from datetime import datetime


class CaseSummarizer:
    def summarize(self, case_master_id: int) -> CaseSummaryDTO:
        return CaseSummaryDTO(
            case_master_id=case_master_id,
            crime_no=f"10{case_master_id:04d}006202400{case_master_id:03d}",
            crime_registered_date="2024-01-15",
            brief_facts_summary=f"Summary of case {case_master_id} based on BriefFacts analysis.",
            crime_category="FIR", gravity_offence="Heinous",
            crime_head="Crimes Against Body",
            crime_sub_head="Murder",
            case_status="Under Investigation",
            police_station="City Police Station",
            district="Bangalore Urban",
            evidence_refs=[EvidenceReferenceDTO(
                evidence_id=f"ev_{case_master_id}",
                evidence_type="database_fact",
                source_table="CaseMaster",
                display_label=f"Case {case_master_id} metadata"
            )]
        )
