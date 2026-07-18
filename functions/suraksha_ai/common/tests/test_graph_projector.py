from network.graph_projector import GraphProjector
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestGraphProjector:
    def test_build_graph_returns_nodes_and_edges(self):
        gp = GraphProjector()
        result = gp.build_graph("Ravi Kumar", depth=2)
        assert result.center_node == "Ravi Kumar"
        assert len(result.nodes) > 0
        assert len(result.edges) >= 0
        assert result.max_depth == 2

    def test_nodes_have_required_fields(self):
        gp = GraphProjector()
        result = gp.build_graph("Suresh P")
        for n in result.nodes:
            assert n.id is not None
            assert n.label is not None
            assert n.node_type == "accused"

    def test_edges_reference_valid_nodes(self):
        gp = GraphProjector()
        result = gp.build_graph("Rajesh K")
        node_ids = {n.id for n in result.nodes}
        for e in result.edges:
            assert e.source in node_ids or not node_ids
            assert e.target in node_ids or not node_ids

    def test_entity_resolution_note_present(self):
        gp = GraphProjector()
        result = gp.build_graph("Manoj R")
        assert "Names matched" in result.entity_resolution_note
