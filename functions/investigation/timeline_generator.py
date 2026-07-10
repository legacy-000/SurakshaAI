from models.dto import TimelineEventDTO


class TimelineGenerator:
    def generate(self, case_master_id: int) -> list[TimelineEventDTO]:
        return [
            TimelineEventDTO(
                event_id=f"ev_{case_master_id}_1",
                event_type="crime_registration",
                event_date="2024-01-15",
                description="FIR registered at City Police Station",
                source_table="CaseMaster",
                source_record_id=case_master_id
            ),
            TimelineEventDTO(
                event_id=f"ev_{case_master_id}_2",
                event_type="arrest",
                event_date="2024-01-18",
                description="Primary accused arrested",
                source_table="ArrestSurrender",
                source_record_id=case_master_id
            ),
            TimelineEventDTO(
                event_id=f"ev_{case_master_id}_3",
                event_type="chargesheet",
                event_date="2024-03-20",
                description="Chargesheet filed (Type A)",
                source_table="ChargesheetDetails",
                source_record_id=case_master_id
            )
        ]
