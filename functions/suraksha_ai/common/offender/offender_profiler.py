from common.models.dto import OffenderProfileDTO


class OffenderProfiler:
    def get_profile(self, accused_name: str) -> OffenderProfileDTO:
        return OffenderProfileDTO(
            entity_id=f"ent_{accused_name.lower().replace(' ', '_')}",
            canonical_name=accused_name,
            name_variants=[accused_name, f"{accused_name.split()[0]} {accused_name.split()[1][0]}."],
            age_range={"min": 28, "max": 42},
            gender="Male",
            case_count=8,
            linked_cases=[
                {"case_id": 101, "crime_no": "CN202400101", "crime_type": "Theft", "year": 2024},
                {"case_id": 201, "crime_no": "CN202400201", "crime_type": "Robbery", "year": 2023},
                {"case_id": 301, "crime_no": "CN202400301", "crime_type": "Assault", "year": 2024},
            ],
            resolution_confidence="medium"
        )
