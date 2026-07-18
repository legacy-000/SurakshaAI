from models.dto import ForecastRequestDTO, GraphProjectionDTO, GraphNodeDTO, GraphEdgeDTO
from analytics.financial_analyzer import FinancialAnalyzer
from forecast.scheduler import ForecastScheduler
from network.graph_projector import GraphProjector
import sys
import os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


def test_centrality_and_communities():
    gp = GraphProjector()
    # Build a simple mock projection (Line graph: node_0 - node_1 - node_2)
    nodes = [
        GraphNodeDTO(id="node_0", label="Ravi Kumar", node_type="accused", cases=3, risk_tier="HIGH"),
        GraphNodeDTO(id="node_1", label="Suresh P", node_type="accused", cases=2, risk_tier="MODERATE"),
        GraphNodeDTO(id="node_2", label="Rajesh K", node_type="accused", cases=1, risk_tier="LOW")
    ]
    edges = [
        GraphEdgeDTO(id="edge_0", source="node_0", target="node_1", weight=1),
        GraphEdgeDTO(id="edge_1", source="node_1", target="node_2", weight=1)
    ]
    projection = GraphProjectionDTO(
        run_id="test_run_123",
        center_node="Ravi Kumar",
        nodes=nodes,
        edges=edges,
        max_depth=2
    )

    result = gp.compute_centrality_and_communities(projection)
    assert result.run_id == "test_run_123"
    assert len(result.communities) > 0
    # Centrality checks
    assert "degree" in result.centrality
    assert "closeness" in result.centrality
    assert "betweenness" in result.centrality

    # Degree centrality of node_1 (middle node) should be 1.0 (degree 2 / (3-1))
    assert result.centrality["degree"]["node_1"] == 1.0
    assert result.centrality["degree"]["Suresh P"] == 1.0

    # Betweenness of node_1 should be 1.0 (since it's on the only path node_0 <-> node_2)
    assert result.centrality["betweenness"]["node_1"] == 1.0


def test_forecast_scheduler():
    scheduler = ForecastScheduler()
    # Confirm singleton
    scheduler2 = ForecastScheduler()
    assert scheduler is scheduler2

    req = ForecastRequestDTO(district_id=18, crime_sub_head_id=10, forecast_horizon_days=5)
    scheduler.schedule_job("test_job", req, interval_seconds=10)

    # Test active jobs
    jobs = scheduler.get_active_jobs()
    assert "test_job" in jobs
    assert jobs["test_job"]["interval_seconds"] == 10

    # Start and stop
    scheduler.start()
    scheduler.stop()

    # Test trigger job now
    result = scheduler.trigger_job_now("test_job")
    assert result is not None
    assert len(result.forecast) == 5

    # Check history
    history = scheduler.get_job_history("test_job")
    assert len(history) >= 1
    assert history[0]["status"] == "success"


def test_financial_analyzer():
    fa = FinancialAnalyzer()

    # Test activity analysis
    activity = fa.analyze_financial_activity("Ravi Kumar")
    assert activity.data_available is True
    assert "Financial Profile Analysis" in activity.message

    # Test shell companies
    shell_companies = fa.detect_shell_companies()
    assert len(shell_companies) >= 4
    for co in shell_companies:
        assert "company_name" in co
        assert "address" in co
        assert "reason" in co

    # Test risk score
    score = fa.compute_financial_risk_score("Ravi Kumar")
    assert 0.0 <= score <= 1.0
