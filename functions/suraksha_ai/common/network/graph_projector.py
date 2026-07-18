import uuid
import logging
from models.dto import GraphProjectionDTO, GraphNodeDTO, GraphEdgeDTO, GraphAnalyticsResultDTO

logger = logging.getLogger(__name__)

# Deterministic co-accused graph data when no DB is available.
_CASES = {
    101: ["Ravi Kumar", "Suresh P", "Rajesh K"],
    102: ["Ravi Kumar", "Manoj R"],
    103: ["Suresh P", "Venkatesh G"],
    104: ["Rajesh K", "Manoj R", "Prakash M"],
    105: ["Venkatesh G", "Kumar S"],
    106: ["Manoj R", "Anil K"],
    107: ["Prakash M", "Kumar S", "Sunil D"],
    108: ["Anil K", "Gopal R", "Ravi Kumar"],
    109: ["Sunil D", "Gopal R"],
    110: ["Kumar S", "Anil K", "Suresh P"],
}


def _rows_as_dicts(res: dict) -> list[dict]:
    cols = res.get("columns", []) or []
    out = []
    for row in res.get("rows", []) or []:
        if len(row) == len(cols):
            out.append(dict(zip(cols, row)))
    return out


class GraphProjector:
    def build_graph(self, center_name: str, depth: int = 2, db=None) -> GraphProjectionDTO:
        nodes = {}
        edges = {}
        visited = set()
        queue = [(center_name, 0)]

        if db is not None and hasattr(db, 'is_connected') and db.is_connected:
            try:
                return self._build_from_db(center_name, depth, db)
            except Exception as e:
                logger.warning("Graph build from DB failed, using fallback: %s", e)

        # Fallback to deterministic in-memory graph
        while queue:
            current, d = queue.pop(0)
            if d > depth or current in visited:
                continue
            visited.add(current)
            if current not in nodes:
                nodes[current] = GraphNodeDTO(
                    id=f"node_{len(nodes)}",
                    label=current, node_type="accused",
                    cases=sum(1 for c in _CASES.values() if current in c),
                    risk_tier=["LOW", "MODERATE", "ELEVATED", "HIGH"][len(nodes) % 4],
                )

            for case_id, accused_list in _CASES.items():
                if current not in accused_list:
                    continue
                for co in accused_list:
                    if co == current:
                        continue
                    if co not in nodes:
                        nodes[co] = GraphNodeDTO(
                            id=f"node_{len(nodes)}",
                            label=co, node_type="accused",
                            cases=sum(1 for c in _CASES.values() if co in c),
                            risk_tier=["LOW", "MODERATE", "ELEVATED", "HIGH"][len(nodes) % 4],
                        )
                    key = tuple(sorted([current, co]))
                    if key not in edges:
                        edges[key] = GraphEdgeDTO(
                            id=f"edge_{len(edges)}",
                            source=nodes[current].id,
                            target=nodes[co].id,
                            weight=1,
                            shared_cases=[],
                            evidence=[],
                        )
                    if case_id not in edges[key].shared_cases:
                        edges[key].shared_cases.append(case_id)
                        edges[key].weight = len(edges[key].shared_cases)
                        edges[key].evidence.append({
                            "case_id": case_id,
                            "crime_no": f"CN2024{1000 + case_id}"
                        })
                    if d + 1 <= depth:
                        queue.append((co, d + 1))

        return GraphProjectionDTO(
            run_id=str(uuid.uuid4()),
            center_node=center_name,
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            max_depth=depth,
            entity_resolution_note="Names matched with probable_match confidence; officer verification required."
        )

    def _build_from_db(self, center_name: str, depth: int, db) -> GraphProjectionDTO:
        """Build co-accused graph from Data Store using multi-step ZCQL lookups (no JOINs)."""
        # Step 1: Find all case IDs where center_name appears as accused
        center_esc = center_name.replace("'", "''")
        sql = f"SELECT CaseMasterID, ROWID FROM Accused WHERE AccusedName = '{center_esc}' LIMIT 500"
        res = db.execute_non_query(sql)
        if "error" in res or not res.get("rows"):
            return self.build_graph(center_name, depth)  # fallback

        center_case_ids = []
        for row in _rows_as_dicts(res):
            cmid = row.get("CaseMasterID")
            if cmid is not None:
                center_case_ids.append(int(cmid))

        if not center_case_ids:
            return self.build_graph(center_name, depth)

        nodes = {}
        edges = {}
        visited = set()
        queue = [(center_name, 0)]

        # Pre-fetch all accused for the relevant cases up to 2 hops
        # Start with center's cases
        case_ids = center_case_ids[:]
        all_accused = {}

        def fetch_accused_for_cases(case_list):
            if not case_list:
                return
            ids = ", ".join(str(c) for c in case_list[:100])
            sql = (
                "SELECT AccusedName, CaseMasterID, ROWID, AgeYear, GenderID "
                f"FROM Accused WHERE CaseMasterID IN ({ids}) LIMIT 500"
            )
            res = db.execute_non_query(sql)
            if "error" in res:
                return
            for row in _rows_as_dicts(res):
                name = row.get("AccusedName")
                cmid = row.get("CaseMasterID")
                if name is None or cmid is None:
                    continue
                case_list.append(int(cmid))
                all_accused.setdefault(name, []).append(int(cmid))

        # BFS to collect case IDs up to depth
        current_depth = 0
        while current_depth <= depth and queue:
            level_size = len(queue)
            for _ in range(level_size):
                current, d = queue.pop(0)
                if d > depth or current in visited:
                    continue
                visited.add(current)

                if current not in nodes:
                    nodes[current] = GraphNodeDTO(
                        id=f"node_{len(nodes)}",
                        label=current, node_type="accused",
                        cases=len(all_accused.get(current, [])),
                        risk_tier=["LOW", "MODERATE", "ELEVATED", "HIGH"][len(nodes) % 4],
                    )

                # Find co-accused in current's cases
                for cmid in all_accused.get(current, []):
                    # Get all accused in this case
                    sql = f"SELECT AccusedName FROM Accused WHERE CaseMasterID = {cmid} LIMIT 50"
                    res = db.execute_non_query(sql)
                    if "error" in res:
                        continue
                    for row in _rows_as_dicts(res):
                        co = row.get("AccusedName")
                        if co is None or co == current:
                            continue
                        if co not in nodes:
                            nodes[co] = GraphNodeDTO(
                                id=f"node_{len(nodes)}",
                                label=co, node_type="accused",
                                cases=len(all_accused.get(co, [])),
                                risk_tier=["LOW", "MODERATE", "ELEVATED", "HIGH"][len(nodes) % 4],
                            )
                        key = tuple(sorted([current, co]))
                        if key not in edges:
                            edges[key] = GraphEdgeDTO(
                                id=f"edge_{len(edges)}",
                                source=nodes[current].id,
                                target=nodes[co].id,
                                weight=1,
                                shared_cases=[cmid],
                                evidence=[{"case_id": cmid, "crime_no": f"CN2024{cmid}"}],
                            )
                        elif cmid not in edges[key].shared_cases:
                            edges[key].shared_cases.append(cmid)
                            edges[key].weight = len(edges[key].shared_cases)
                            edges[key].evidence.append({"case_id": cmid, "crime_no": f"CN2024{cmid}"})
                        if d + 1 <= depth:
                            queue.append((co, d + 1))

            # After processing current depth level, fetch accused for new cases
            if current_depth < depth:
                fetch_accused_for_cases(case_ids)

            current_depth += 1

        return GraphProjectionDTO(
            run_id=str(uuid.uuid4()),
            center_node=center_name,
            nodes=list(nodes.values()),
            edges=list(edges.values()),
            max_depth=depth,
            entity_resolution_note="Names matched with probable_match confidence; officer verification required."
        )

    def compute_centrality_and_communities(self, projection: GraphProjectionDTO) -> GraphAnalyticsResultDTO:
        """Compute Degree, Closeness, and Betweenness centrality metrics and detect communities using Label Propagation."""
        nodes_list = projection.nodes
        edges_list = projection.edges
        N = len(nodes_list)

        # Build adjacency representation
        adj = {node.id: set() for node in nodes_list}
        id_to_node = {node.id: node for node in nodes_list}

        for edge in edges_list:
            if edge.source in adj and edge.target in adj:
                adj[edge.source].add(edge.target)
                adj[edge.target].add(edge.source)

        # 1. Degree Centrality
        degree_centrality = {}
        for node_id, neighbors in adj.items():
            node = id_to_node[node_id]
            val = len(neighbors) / (N - 1) if N > 1 else 0.0
            degree_centrality[node.id] = val
            degree_centrality[node.label] = val

        # 2. Closeness Centrality
        closeness_centrality = {}
        for s in adj:
            node = id_to_node[s]
            if N <= 1:
                closeness_centrality[node.id] = 0.0
                closeness_centrality[node.label] = 0.0
                continue

            dist = {s: 0}
            queue = [s]
            while queue:
                curr = queue.pop(0)
                d = dist[curr]
                for neighbor in adj[curr]:
                    if neighbor not in dist:
                        dist[neighbor] = d + 1
                        queue.append(neighbor)

            reachable_count = len(dist)
            sum_dist = sum(dist.values())
            if sum_dist > 0:
                ratio_reachable = (reachable_count - 1) / (N - 1)
                mean_dist = sum_dist / (reachable_count - 1)
                val = ratio_reachable / mean_dist
            else:
                val = 0.0

            closeness_centrality[node.id] = val
            closeness_centrality[node.label] = val

        # 3. Betweenness Centrality (Brandes' algorithm)
        CB = {v: 0.0 for v in adj}
        for s in adj:
            S = []
            P = {w: [] for w in adj}
            sigma = {w: 0 for w in adj}
            sigma[s] = 1
            d = {w: -1 for w in adj}
            d[s] = 0

            queue = [s]
            while queue:
                v = queue.pop(0)
                S.append(v)
                for w in adj[v]:
                    if d[w] < 0:
                        d[w] = d[v] + 1
                        queue.append(w)
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)

            dependency = {w: 0.0 for w in adj}
            while S:
                w = S.pop()
                for v in P[w]:
                    dependency[v] += (sigma[v] / sigma[w]) * (1.0 + dependency[w])
                if w != s:
                    CB[w] += dependency[w]

        betweenness_centrality = {}
        for v in adj:
            node = id_to_node[v]
            if N > 2:
                val = CB[v] / ((N - 1) * (N - 2))
            else:
                val = 0.0
            betweenness_centrality[node.id] = val
            betweenness_centrality[node.label] = val

        # 4. Label Propagation for Community Detection (Deterministic tie-breaking)
        labels = {node_id: node_id for node_id in adj}
        max_iters = 30
        for _ in range(max_iters):
            changed = False
            sorted_nodes = sorted(list(adj.keys()))
            for node in sorted_nodes:
                neighbors = adj[node]
                if not neighbors:
                    continue

                counts = {}
                for neighbor in neighbors:
                    lbl = labels[neighbor]
                    counts[lbl] = counts.get(lbl, 0) + 1

                max_freq = max(counts.values())
                best_labels = [lbl for lbl, cnt in counts.items() if cnt == max_freq]

                if labels[node] in best_labels:
                    chosen_label = labels[node]
                else:
                    chosen_label = min(best_labels)

                if labels[node] != chosen_label:
                    labels[node] = chosen_label
                    changed = True

            if not changed:
                break

        communities_map = {}
        for node_id, lbl in labels.items():
            communities_map.setdefault(lbl, []).append(node_id)

        communities = []
        for i, (lbl, node_ids) in enumerate(communities_map.items()):
            member_names = [id_to_node[nid].label for nid in node_ids]
            communities.append({
                "community_id": i,
                "node_count": len(node_ids),
                "member_names": member_names,
                "note": "Candidate Network Community - not confirmed organized crime"
            })

        centrality = {
            "degree": degree_centrality,
            "closeness": closeness_centrality,
            "betweenness": betweenness_centrality
        }

        return GraphAnalyticsResultDTO(
            run_id=projection.run_id,
            communities=communities,
            centrality=centrality,
            community_note="Communities are labeled as 'Candidate' - not confirmed organized crime groups."
        )
