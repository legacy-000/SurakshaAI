import uuid
from models.dto import GraphProjectionDTO, GraphNodeDTO, GraphEdgeDTO

_CASE_CONNECTIONS = {
    "Ravi Kumar": {"cases": [101, 102, 108], "risk": "ELEVATED", "crime_type": "Theft"},
    "Suresh P": {"cases": [101, 103, 110], "risk": "MODERATE", "crime_type": "Robbery"},
    "Rajesh K": {"cases": [101, 104], "risk": "ELEVATED", "crime_type": "Theft"},
    "Manoj R": {"cases": [102, 104, 106], "risk": "MODERATE", "crime_type": "Burglary"},
    "Venkatesh G": {"cases": [103], "risk": "LOW", "crime_type": "Robbery"},
    "Prakash M": {"cases": [104, 107], "risk": "MODERATE", "crime_type": "Assault"},
    "Kumar S": {"cases": [105, 107, 110], "risk": "HIGH", "crime_type": "Cyber Crime"},
    "Anil K": {"cases": [106, 108, 110], "risk": "ELEVATED", "crime_type": "Burglary"},
    "Sunil D": {"cases": [107, 109], "risk": "LOW", "crime_type": "Assault"},
    "Gopal R": {"cases": [108, 109], "risk": "MODERATE", "crime_type": "Theft"},
}


def _compute_risk_tier(case_count: int) -> str:
    if case_count >= 6: return "HIGH"
    if case_count >= 4: return "ELEVATED"
    if case_count >= 2: return "MODERATE"
    return "LOW"


def _connection_label(shared_cases: list[int], name_a: str, name_b: str) -> str:
    if not shared_cases:
        return "co-accused"
    case_nos = [f"#{c}" for c in shared_cases[:3]]
    label = f"co-accused in {', '.join(case_nos)}"
    if len(shared_cases) > 3:
        label += f" +{len(shared_cases)-3} more"
    return label


class GraphProjector:
    def build_graph(self, center_name: str, depth: int = 2) -> GraphProjectionDTO:
        nodes: dict[str, GraphNodeDTO] = {}
        edges: dict[tuple, GraphEdgeDTO] = {}
        visited: set[str] = set()
        queue = [(center_name, 0)]

        while queue:
            current, d = queue.pop(0)
            if d > depth or current in visited:
                continue
            visited.add(current)

            data = _CASE_CONNECTIONS.get(current)
            if not data:
                for name, info in _CASE_CONNECTIONS.items():
                    if center_name.lower() in name.lower() or name.lower() in center_name.lower():
                        data = info
                        current = name
                        break
                if not data:
                    continue

            if current not in nodes:
                nodes[current] = GraphNodeDTO(
                    id=f"node_{len(nodes)}",
                    label=current, node_type="accused",
                    cases=len(data["cases"]),
                    risk_tier=_compute_risk_tier(len(data["cases"])),
                    crime_type=data.get("crime_type", "Unknown"),
                )

            for name, info in _CASE_CONNECTIONS.items():
                if name == current:
                    continue
                shared = sorted(set(data["cases"]) & set(info["cases"]))
                if not shared:
                    continue
                if name not in nodes:
                    nodes[name] = GraphNodeDTO(
                        id=f"node_{len(nodes)}",
                        label=name, node_type="accused",
                        cases=len(info["cases"]),
                        risk_tier=_compute_risk_tier(len(info["cases"])),
                        crime_type=info.get("crime_type", "Unknown"),
                    )
                key = tuple(sorted([current, name]))
                if key not in edges:
                    edges[key] = GraphEdgeDTO(
                        id=f"edge_{len(edges)}",
                        source=nodes[current].id,
                        target=nodes[name].id,
                        weight=len(shared),
                        shared_cases=shared,
                        evidence=[{"case_id": c, "crime_no": f"CN2024{1000+c}"} for c in shared],
                        connection_basis=_connection_label(shared, current, name),
                    )
                if d + 1 <= depth:
                    queue.append((name, d + 1))

        return GraphProjectionDTO(
            run_id=str(uuid.uuid4()),
            center_node=center_name,
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            max_depth=depth,
            entity_resolution_note="Names matched with probable_match confidence; officer verification required."
        )