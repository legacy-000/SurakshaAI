from typing import List, Dict, Any
from models.datastore_models import CaseMaster, Accused


class NetworkAnalyzer:
    """
    Builds association networks linking cases, accused, victims, and locations.
    Produces node-edge graph data for the front-end visualization layer.
    """

    def __init__(self):
        self._case_model = CaseMaster()
        self._accused_model = Accused()

    def build_network_graph(self, nodes: List[Dict[str, Any]] = None, edges: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        if nodes and edges:
            return {"nodes": nodes, "edges": edges}

        cases = self._case_model.get_all()
        accused = self._accused_model.get_all()

        result_nodes = []
        result_edges = []
        seen = set()

        if cases:
            for c in cases:
                cid = c.get("CaseMasterID", "")
                if cid and cid not in seen:
                    result_nodes.append({
                        "id": str(cid), "label": f"Case #{cid}",
                        "type": "case", "group": 1
                    })
                    seen.add(cid)

        if accused:
            name_counter = {}
            for a in accused:
                name = a.get("AccusedName", "Unknown")
                name_counter[name] = name_counter.get(name, 0) + 1
                node_id = f"accused_{name}_{name_counter[name]}"
                result_nodes.append({
                    "id": node_id, "label": name,
                    "type": "accused", "group": 2
                })
                cid = a.get("CaseMasterID", "")
                if cid in seen:
                    result_edges.append({
                        "source": node_id, "target": str(cid), "relation": "accused_in"
                    })

        return {"nodes": result_nodes, "edges": result_edges, "graph": "network_graph_data"}
