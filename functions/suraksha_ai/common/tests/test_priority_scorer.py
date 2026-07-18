from offender.priority_scorer import PriorityScorer
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestPriorityScorer:
    def test_calculate_score_returns_all_six_features(self):
        ps = PriorityScorer()
        score = ps.calculate_score("ent_test", "Ravi Kumar")
        assert len(score.features) == 6
        assert score.entity_name == "Ravi Kumar"

    def test_feature_names_match_expected(self):
        ps = PriorityScorer()
        score = ps.calculate_score("ent_test", "Ravi Kumar")
        names = [f.name for f in score.features]
        assert "Case Frequency" in names
        assert "Crime Type Diversity" in names
        assert "Geographic Spread" in names
        assert "Recent Activity Frequency" in names
        assert "Co Accused Network Size" in names
        assert "Arrest Surrender Ratio" in names

    def test_risk_tier_is_valid(self):
        ps = PriorityScorer()
        score = ps.calculate_score("ent_test", "Ravi Kumar")
        assert score.risk_tier in ("LOW", "MODERATE", "ELEVATED", "HIGH")

    def test_score_is_deterministic(self):
        ps = PriorityScorer()
        s1 = ps.calculate_score("ent_test", "Ravi Kumar")
        s2 = ps.calculate_score("ent_test", "Ravi Kumar")
        assert s1.total_score == s2.total_score
        assert s1.risk_tier == s2.risk_tier
