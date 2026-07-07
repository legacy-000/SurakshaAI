import random
from models.dto import GraphAnalyticsResultDTO


class GraphAnalyzer:
    def analyze(self, run_id: str) -> GraphAnalyticsResultDTO:
        num_communities = random.randint(2, 4)
        communities = [
            {
                "community_id": i,
                "node_count": random.randint(3, 8),
                "member_names": [f"Accused_{random.randint(1, 20)}" for _ in range(3)],
                "note": "Candidate Network Community - not confirmed organized crime"
            }
            for i in range(num_communities)
        ]

        centrality = {
            "degree": {f"node_{i}": random.random() for i in range(10)},
            "betweenness": {f"node_{i}": random.random() * 0.5 for i in range(10)},
        }

        return GraphAnalyticsResultDTO(
            run_id=run_id,
            communities=communities,
            centrality=centrality,
            community_note="Communities are labeled as 'Candidate' - not confirmed organized crime groups."
        )
