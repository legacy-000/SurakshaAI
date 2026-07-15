from models.dto import TimelineEventDTO

# ponytail: deterministic timeline based on case_master_id, query real DB when Data Store is live


class TimelineGenerator:
    def generate(self, case_master_id: int) -> list[TimelineEventDTO]:
        base_case = case_master_id % 100
        month = max(1, base_case % 12)
        day = max(1, base_case % 28)
        return [
            TimelineEventDTO(
                event_id=f"ev_{case_master_id}_reg",
                event_type="crime_registration",
                event_date=f"2025-{month:02d}-{day:02d}",
                description="FIR registered at police station",
                source_table="CaseMaster", source_record_id=case_master_id
            ),
            TimelineEventDTO(
                event_id=f"ev_{case_master_id}_arr",
                event_type="arrest",
                event_date=f"2025-{min(month+1,12):02d}-{day:02d}",
                description="Primary accused arrested",
                source_table="ArrestSurrender", source_record_id=case_master_id
            ),
            TimelineEventDTO(
                event_id=f"ev_{case_master_id}_chg",
                event_type="chargesheet",
                event_date=f"2025-{min(month+3,12):02d}-{day:02d}",
                description="Chargesheet filed",
                source_table="ChargesheetDetails", source_record_id=case_master_id
            ),
        ]
