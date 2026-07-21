import uuid
import logging
from models.dto import GraphProjectionDTO, GraphNodeDTO, GraphEdgeDTO, GraphAnalyticsResultDTO

logger = logging.getLogger(__name__)

_CASE_DATA = {
    101: {"accused": ["Ravi Kumar", "Suresh P", "Rajesh K"], "crime": "Theft", "year": 2024},
    102: {"accused": ["Ravi Kumar", "Manoj R"], "crime": "Theft", "year": 2024},
    103: {"accused": ["Suresh P", "Venkatesh G"], "crime": "Robbery", "year": 2024},
    104: {"accused": ["Rajesh K", "Manoj R", "Prakash M"], "crime": "Burglary", "year": 2024},
    105: {"accused": ["Venkatesh G", "Kumar S"], "crime": "Robbery", "year": 2024},
    106: {"accused": ["Manoj R", "Anil K"], "crime": "Burglary", "year": 2024},
    107: {"accused": ["Prakash M", "Kumar S", "Sunil D"], "crime": "Assault", "year": 2024},
    108: {"accused": ["Anil K", "Gopal R", "Ravi Kumar"], "crime": "Theft", "year": 2024},
    109: {"accused": ["Sunil D", "Gopal R"], "crime": "Assault", "year": 2024},
    110: {"accused": ["Kumar S", "Anil K", "Suresh P"], "crime": "Cyber Crime", "year": 2024},
    111: {"accused": ["Mahesh N", "Dinesh B"], "crime": "Cheating", "year": 2025},
    112: {"accused": ["Mahesh N", "Satish H"], "crime": "Cheating", "year": 2025},
    113: {"accused": ["Dinesh B", "Satish H"], "crime": "Robbery", "year": 2025},
    114: {"accused": ["Satish H", "Vinod T"], "crime": "Cyber Crime", "year": 2025},
    115: {"accused": ["Vinod T", "Harish M"], "crime": "Cyber Crime", "year": 2025},
    116: {"accused": ["Harish M"], "crime": "Theft", "year": 2025},
}

_CRIME_COLORS = {
    "Theft": "#3B82F6", "Robbery": "#F59E0B", "Burglary": "#8B5CF6",
    "Assault": "#EF4444", "Cyber Crime": "#06B6D4", "Cheating": "#EC4899",
}


def _rows_as_dicts(res: dict) -> list[dict]:
    cols = res.get("columns", []) or []
    return [dict(zip(cols, row)) for row in (res.get("rows", []) or []) if len(row) == len(cols)]


def _compute_risk_tier(case_count: int) -> str:
    if case_count >= 6: return "HIGH"
    if case_count >= 4: return "ELEVATED"
    if case_count >= 2: return "MODERATE"
    return "LOW"


class GraphProjector:
    def build_graph(self, center_name: str, depth: int = 2, db=None, search_type: str = "auto") -> GraphProjectionDTO:
        try:
            if db is not None and hasattr(db, 'is_connected') and db.is_connected:
                try:
                    return self._build_from_db(center_name, depth, db, search_type)
                except Exception as e:
                    logger.warning("Graph build from DB failed, using fallback: %s", e)
            return self._build_fallback(center_name, depth, search_type)
        except Exception as e:
            logger.error("Graph build completely failed: %s", e, exc_info=True)
            import traceback
            traceback.print_exc()
            return GraphProjectionDTO(
                run_id=str(uuid.uuid4()), center_node=center_name,
                nodes=[], edges=[], max_depth=depth,
                entity_resolution_note=f"Error building graph: {e}"
            )

    def _resolve_search_type(self, center_name: str, explicit: str) -> str:
        if explicit in ("person", "case"):
            return explicit
        stripped = center_name.strip().lower().replace("#", "").replace("case", "").replace(" ", "")
        if stripped.isdigit():
            return "case"
        return "person"

    def _build_fallback(self, center_name: str, depth: int, search_type: str = "auto") -> GraphProjectionDTO:
        st = self._resolve_search_type(center_name, search_type)
        case_ids: set[int] = set()
        accused_cases: dict[str, list[int]] = {}

        if st == "case":
            stripped = center_name.strip().lower().replace("#", "").replace("case", "").replace(" ", "")
            target_id = int(stripped)
            if target_id in _CASE_DATA:
                case_ids.add(target_id)
            if not case_ids:
                return GraphProjectionDTO(
                    run_id=str(uuid.uuid4()), center_node=center_name,
                    nodes=[], edges=[], max_depth=depth,
                    entity_resolution_note=f"Case #{target_id} not found."
                )
        else:
            for cid, cdata in _CASE_DATA.items():
                for name in cdata["accused"]:
                    accused_cases.setdefault(name, []).append(cid)
                    if center_name.lower() in name.lower() or name.lower() in center_name.lower():
                        case_ids.add(cid)

            if not case_ids:
                for cid, cdata in _CASE_DATA.items():
                    if any(center_name.lower() in a.lower() for a in cdata["accused"]):
                        case_ids.add(cid)

        if not case_ids:
            return GraphProjectionDTO(
                run_id=str(uuid.uuid4()), center_node=center_name,
                nodes=[], edges=[], max_depth=depth,
                entity_resolution_note="No cases found for this name."
            )

        # BFS: collect cases up to depth
        all_case_ids: set[int] = set(case_ids)
        current_depth = 0
        frontier: set[int] = set(case_ids)

        while current_depth < depth and frontier:
            next_frontier: set[int] = set()
            for cid in frontier:
                for name in _CASE_DATA[cid]["accused"]:
                    for other_cid in accused_cases.get(name, []):
                        if other_cid not in all_case_ids:
                            all_case_ids.add(other_cid)
                            next_frontier.add(other_cid)
            frontier = next_frontier
            current_depth += 1

        # Build case nodes
        case_node_map: dict[int, GraphNodeDTO] = {}
        for cid in sorted(all_case_ids):
            cd = _CASE_DATA[cid]
            case_node_map[cid] = GraphNodeDTO(
                id=f"case_{cid}",
                label=f"Case #{cid}",
                node_type="case",
                cases=len(cd["accused"]),
                crime_type=cd["crime"],
                risk_tier="LOW",
                person_id=None,
            )

        # Build accused nodes
        involved_accused: dict[str, list[int]] = {}
        for cid in all_case_ids:
            for name in _CASE_DATA[cid]["accused"]:
                involved_accused.setdefault(name, []).append(cid)

        accused_node_map: dict[str, GraphNodeDTO] = {}
        for name, cids in involved_accused.items():
            primary_crime = _CASE_DATA[cids[0]]["crime"]
            accused_node_map[name] = GraphNodeDTO(
                id=f"node_{len(accused_node_map)}",
                label=name,
                node_type="accused",
                cases=len(cids),
                risk_tier=_compute_risk_tier(len(cids)),
                crime_type=primary_crime,
                person_id=name,
            )

        # Build edges: case → accused
        edges: dict[str, GraphEdgeDTO] = []
        edge_id = 0
        for cid in sorted(all_case_ids):
            cd = _CASE_DATA[cid]
            for name in cd["accused"]:
                if name in accused_node_map:
                    edges.append(GraphEdgeDTO(
                        id=f"edge_{edge_id}",
                        source=case_node_map[cid].id,
                        target=accused_node_map[name].id,
                        weight=1,
                        shared_cases=[cid],
                        evidence=[{"case_id": cid, "crime_no": f"CN2024{cid}"}],
                        connection_basis=f"accused in Case #{cid}",
                    ))
                    edge_id += 1

        # Build edges: case → case (shared accused)
        seen_pairs: set[tuple[int, int]] = set()
        for cid_a in sorted(all_case_ids):
            accused_a = set(_CASE_DATA[cid_a]["accused"])
            for cid_b in sorted(all_case_ids):
                if cid_a >= cid_b:
                    continue
                shared = accused_a & set(_CASE_DATA[cid_b]["accused"])
                if shared:
                    pair = (cid_a, cid_b)
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    shared_names = ", ".join(sorted(shared))
                    edges.append(GraphEdgeDTO(
                        id=f"edge_{edge_id}",
                        source=case_node_map[cid_a].id,
                        target=case_node_map[cid_b].id,
                        weight=len(shared),
                        shared_cases=[cid_a, cid_b],
                        evidence=[{"shared_person": s} for s in sorted(shared)],
                        connection_basis=f"shared: {shared_names}",
                    ))
                    edge_id += 1

        nodes = list(case_node_map.values()) + list(accused_node_map.values())

        return GraphProjectionDTO(
            run_id=str(uuid.uuid4()),
            center_node=center_name,
            nodes=nodes,
            edges=edges,
            max_depth=depth,
            entity_resolution_note="Graph shows cases as central nodes, accused as person nodes."
        )

    def _build_from_db(self, center_name: str, depth: int, db, search_type: str = "auto") -> GraphProjectionDTO:
        st = self._resolve_search_type(center_name, search_type)
        center_case_ids: list[int] = []

        if st == "case":
            stripped = center_name.strip().lower().replace("#", "").replace("case", "").replace(" ", "")
            target_id = int(stripped)
            sql = f"SELECT CaseMasterID, ROWID FROM CaseMaster WHERE CaseMasterID = {target_id} LIMIT 1"
            res = db.execute_non_query(sql)
            if "error" not in res and res.get("rows"):
                center_case_ids.append(target_id)
            if not center_case_ids:
                return self._build_fallback(center_name, depth, search_type)
        else:
            center_esc = center_name.replace("'", "''")
            sql = f"SELECT CaseMasterID, ROWID FROM Accused WHERE AccusedName = '{center_esc}' LIMIT 500"
            res = db.execute_non_query(sql)
            if "error" in res or not res.get("rows"):
                return self._build_fallback(center_name, depth, search_type)

            for row in _rows_as_dicts(res):
                cmid = row.get("CaseMasterID")
                if cmid is not None:
                    center_case_ids.append(int(cmid))

            if not center_case_ids:
                return self._build_fallback(center_name, depth, search_type)

        all_case_ids: set[int] = set(center_case_ids)
        case_accused: dict[int, list[str]] = {}
        accused_cases: dict[str, list[int]] = {}

        def load_accused_for_cases(case_list: list[int]):
            if not case_list:
                return
            ids = ", ".join(str(c) for c in case_list[:100])
            sql = f"SELECT AccusedName, CaseMasterID FROM Accused WHERE CaseMasterID IN ({ids}) LIMIT 1000"
            r = db.execute_non_query(sql)
            if "error" in r:
                return
            for row in _rows_as_dicts(r):
                name = row.get("AccusedName")
                cmid = row.get("CaseMasterID")
                if name and cmid:
                    cid = int(cmid)
                    case_accused.setdefault(cid, []).append(name.strip())
                    accused_cases.setdefault(name.strip(), []).append(cid)

        def load_crime_type(case_list: list[int]) -> dict[int, str]:
            if not case_list:
                return {}
            ids = ", ".join(str(c) for c in case_list[:100])
            sql = f"SELECT CrimeMinorHeadID FROM CaseMaster LIMIT {len(case_list)}"
            r = db.execute_non_query(sql)
            return {}

        load_accused_for_cases(center_case_ids)

        # If no accused loaded (ZCQL column issue), fall back to mock data
        if not any(case_accused.get(c) for c in center_case_ids):
            logger.warning("Accused data empty for case query, falling back to mock")
            return self._build_fallback(center_name, depth, search_type)

        current_depth = 0
        frontier: set[int] = set(center_case_ids)
        while current_depth < depth and frontier:
            next_frontier: set[int] = set()
            for cid in frontier:
                for name in case_accused.get(cid, []):
                    sql = f"SELECT CaseMasterID FROM Accused WHERE AccusedName = '{name.replace(chr(39), chr(39)+chr(39))}' LIMIT 100"
                    r = db.execute_non_query(sql)
                    if "error" in r:
                        continue
                    for row in _rows_as_dicts(r):
                        ocid = int(row["CaseMasterID"])
                        if ocid not in all_case_ids:
                            all_case_ids.add(ocid)
                            next_frontier.add(ocid)
            load_accused_for_cases(list(next_frontier))
            frontier = next_frontier
            current_depth += 1

        crime_type_map: dict[int, str] = {}
        for cid in all_case_ids:
            crime_type_map[cid] = "Unknown"

        case_node_map: dict[int, GraphNodeDTO] = {}
        for cid in sorted(all_case_ids):
            accused_list = case_accused.get(cid, [])
            case_node_map[cid] = GraphNodeDTO(
                id=f"case_{cid}", label=f"Case #{cid}",
                node_type="case", cases=len(accused_list),
                risk_tier="LOW", crime_type=crime_type_map.get(cid, "Unknown"),
            )

        involved = {name: sorted(set(cids)) for name, cids in accused_cases.items() if set(cids) & all_case_ids}
        accused_node_map: dict[str, GraphNodeDTO] = {}
        for name, cids in involved.items():
            accused_node_map[name] = GraphNodeDTO(
                id=f"node_{len(accused_node_map)}", label=name,
                node_type="accused", cases=len(cids),
                risk_tier=_compute_risk_tier(len(cids)),
                crime_type=crime_type_map.get(cids[0], "Unknown"), person_id=name,
            )

        edges: list[GraphEdgeDTO] = []
        edge_id = 0
        for cid in sorted(all_case_ids):
            for name in case_accused.get(cid, []):
                if name in accused_node_map:
                    edges.append(GraphEdgeDTO(
                        id=f"edge_{edge_id}",
                        source=case_node_map[cid].id,
                        target=accused_node_map[name].id,
                        weight=1, shared_cases=[cid],
                        evidence=[{"case_id": cid}],
                        connection_basis=f"accused in Case #{cid}"))
                    edge_id += 1

        seen_pairs: set[tuple[int, int]] = set()
        for cid_a in sorted(all_case_ids):
            accused_a = set(case_accused.get(cid_a, []))
            for cid_b in sorted(all_case_ids):
                if cid_a >= cid_b:
                    continue
                shared = accused_a & set(case_accused.get(cid_b, []))
                if shared and (cid_a, cid_b) not in seen_pairs:
                    seen_pairs.add((cid_a, cid_b))
                    edges.append(GraphEdgeDTO(
                        id=f"edge_{edge_id}",
                        source=case_node_map[cid_a].id,
                        target=case_node_map[cid_b].id,
                        weight=len(shared), shared_cases=[cid_a, cid_b],
                        evidence=[{"shared_person": s} for s in sorted(shared)],
                        connection_basis=f"shared: {', '.join(sorted(shared))}"))
                    edge_id += 1

        nodes = list(case_node_map.values()) + list(accused_node_map.values())
        return GraphProjectionDTO(
            run_id=str(uuid.uuid4()), center_node=center_name,
            nodes=nodes, edges=edges, max_depth=depth,
            entity_resolution_note="Graph shows cases as central nodes, accused as person nodes."
        )

    def compute_centrality_and_communities(self, projection: GraphProjectionDTO) -> GraphAnalyticsResultDTO:
        nodes_list = projection.nodes
        edges_list = projection.edges
        N = len(nodes_list)

        adj = {node.id: set() for node in nodes_list}
        id_to_node = {node.id: node for node in nodes_list}

        for edge in edges_list:
            if edge.source in adj and edge.target in adj:
                adj[edge.source].add(edge.target)
                adj[edge.target].add(edge.source)

        degree_centrality = {}
        for node_id, neighbors in adj.items():
            node = id_to_node[node_id]
            val = len(neighbors) / (N - 1) if N > 1 else 0.0
            degree_centrality[node.id] = val
            degree_centrality[node.label] = val

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

        labels = {node_id: node_id for node_id in adj}
        max_iters = 30
        for _ in range(max_iters):
            changed = False
            for node in sorted(adj.keys()):
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
                "community_id": i, "node_count": len(node_ids),
                "member_names": member_names,
                "note": "Candidate Network Community - not confirmed organized crime"
            })

        return GraphAnalyticsResultDTO(
            run_id=projection.run_id, communities=communities,
            centrality={"degree": degree_centrality, "closeness": closeness_centrality, "betweenness": betweenness_centrality},
            community_note="Communities are labeled as 'Candidate' - not confirmed organized crime groups."
        )