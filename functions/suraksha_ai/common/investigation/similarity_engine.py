import random
from common.models.dto import SimilarCaseDTO


class SimilarityEngine:
    def find_similar(self, case_master_id: int, top_k: int = 5) -> list[SimilarCaseDTO]:
        return [
            SimilarCaseDTO(
                case_master_id=random.randint(100, 500),
                similarity_score=round(random.uniform(0.7, 0.95), 4),
                crime_no=f"CN2024{random.randint(1000,9999)}",
                crime_sub_head=["Murder", "Theft", "Robbery", "Assault", "Burglary"][i],
                crime_registered_date=f"2024-{random.randint(1,6):02d}-{random.randint(1,28):02d}",
                district_name=["Bangalore", "Mysuru", "Hubli", "Mangalore"][i % 4],
                per_feature_scores={
                    "crime_type": round(random.uniform(0.8, 1.0), 2),
                    "time_proximity": round(random.uniform(0.6, 0.9), 2),
                    "location": round(random.uniform(0.5, 0.9), 2),
                    "text_embedding": round(random.uniform(0.7, 0.95), 2)
                }
            )
            for i in range(min(top_k, 5))
        ]
