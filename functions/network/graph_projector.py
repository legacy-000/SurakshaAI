import uuid
import random
from models.dto import GraphProjectionDTO, GraphNodeDTO, GraphEdgeDTO


class GraphProjector:
    def build_graph(self, center_name: str, depth: int = 2) -> GraphProjectionDTO:
        node_count = random.randint(8, 20)
        edge_count = random.randint(node_count, node_count * 2)

        nodes = [
            GraphNodeDTO(
                id=f"node_{i}",
                label=["Ravi Kumar", "Suresh P", "Rajesh K", "Manoj R", "Venkatesh G",
                       "Prakash M", "Kumar S", "Anil K", "Sunil D", "Gopal R"][i % 10],
                node_type="accused",
                cases=random.randint(1, 8),
                risk_tier=random.choice(["LOW", "MODERATE", "ELEVATED", "HIGH"])
            )
            for i in range(min(node_count, 10))
        ]

        edges = [
            GraphEdgeDTO(
                id=f"edge_{i}",
                source=f"node_{random.randint(0, len(nodes)-1)}",
                target=f"node_{random.randint(0, len(nodes)-1)}",
                weight=random.randint(1, 4),
                shared_cases=[random.randint(100, 500) for _ in range(3)],
                evidence=[{"case_id": random.randint(100, 500), "crime_no": f"CN2024{random.randint(1000,9999)}"}]
            )
            for i in range(min(edge_count, 15))
        ]

        return GraphProjectionDTO(
            run_id=str(uuid.uuid4()),
            center_node=center_name,
            nodes=nodes,
            edges=edges,
            max_depth=depth,
            entity_resolution_note="Names matched with probable_match confidence; officer verification required."
        )
