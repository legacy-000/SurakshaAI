import random
from models.dto import SociologicalAnalysisRequestDTO, SociologicalAnalysisResultDTO, EvidenceReferenceDTO


class SociologicalAnalyzer:
    def analyze(self, req: SociologicalAnalysisRequestDTO) -> SociologicalAnalysisResultDTO:
        distributions = []
        groups = [
            {"group": "18-25", "count": random.randint(100, 500)},
            {"group": "26-35", "count": random.randint(200, 800)},
            {"group": "36-45", "count": random.randint(100, 400)},
            {"group": "46-60", "count": random.randint(50, 200)},
            {"group": "60+", "count": random.randint(10, 100)}
        ]
        total = sum(g["count"] for g in groups)
        suppressed = [g for g in groups if g["count"] < 5]

        for g in groups:
            if g["count"] >= 5:
                g["percentage"] = round(g["count"] / total * 100, 1)
            else:
                g["display"] = "Suppressed: insufficient sample"
            distributions.append(g)

        return SociologicalAnalysisResultDTO(
            query_id="socio_mock_id",
            distributions=distributions,
            sample_size=total,
            missing_data_pct=round(random.uniform(2, 15), 1),
            suppressed_groups=len(suppressed),
            privacy_note="Groups with fewer than 5 individuals are suppressed to protect privacy."
        )
