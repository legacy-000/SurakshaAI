import uuid
from common.models.dto import EntityResolutionRequestDTO, EntityResolutionResultDTO, EntityResolutionCandidate
from common.config.constants import (
    ENTITY_TIER_EXACT_RECORD, ENTITY_TIER_DETERMINISTIC,
    ENTITY_TIER_PROBABLE, ENTITY_TIER_UNRESOLVED
)


class EntityResolver:
    def __init__(self):
        self._known_accused = {
            "Ravi Kumar": [
                {"id": 1, "name": "Ravi Kumar", "case_id": 101, "age": 35, "gender": 1},
                {"id": 2, "name": "Ravi K.", "case_id": 201, "age": 34, "gender": 1},
                {"id": 3, "name": "Ravi S.", "case_id": 301, "age": 28, "gender": 1},
            ],
            "Suresh P": [
                {"id": 4, "name": "Suresh P", "case_id": 102, "age": 42, "gender": 1},
                {"id": 5, "name": "Suresh Patil", "case_id": 202, "age": 43, "gender": 1},
            ]
        }

    def resolve(self, req: EntityResolutionRequestDTO) -> EntityResolutionResultDTO:
        candidates = []
        search = req.accused_name.strip()
        exact_matches = self._known_accused.get(search, [])

        for record in exact_matches:
            tier = ENTITY_TIER_EXACT_RECORD
            score = 100.0
            candidates.append(EntityResolutionCandidate(
                candidate_id=str(uuid.uuid4()),
                accused_master_id=record["id"],
                accused_name=record["name"],
                case_master_id=record["case_id"],
                age_year=record.get("age"),
                gender_id=record.get("gender"),
                match_type=tier,
                match_score=score,
                match_features={"name_similarity": 1.0}
            ))

        if not candidates:
            for name, records in self._known_accused.items():
                if search.lower() in name.lower() or name.lower() in search.lower():
                    for record in records:
                        candidates.append(EntityResolutionCandidate(
                            candidate_id=str(uuid.uuid4()),
                            accused_master_id=record["id"],
                            accused_name=record["name"],
                            case_master_id=record["case_id"],
                            match_type=ENTITY_TIER_PROBABLE,
                            match_score=85.0,
                            match_features={"partial_name_match": True}
                        ))

        return EntityResolutionResultDTO(
            query_id=str(uuid.uuid4()),
            search_name=search,
            candidates=candidates,
            resolution_note="Names matched with probable_match confidence; officer verification required."
        )
