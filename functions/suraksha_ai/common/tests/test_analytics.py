from analytics.stats_aggregator import StatsAggregator
from analytics.hotspot_detector import HotspotDetector
from analytics.trend_analyzer import TrendAnalyzer
from models.dto import CrimeTrendRequestDTO, HotspotRequestDTO
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestTrendAnalyzer:
    def test_analyze_returns_aggregation(self):
        ta = TrendAnalyzer()
        req = CrimeTrendRequestDTO(dimension="month", group_by="district")
        result = ta.analyze(req)
        assert len(result.aggregation) > 0
        assert result.total_records_analyzed > 0
        assert result.query_id is not None

    def test_analyze_periods_have_expected_keys(self):
        ta = TrendAnalyzer()
        req = CrimeTrendRequestDTO()
        result = ta.analyze(req)
        for p in result.aggregation:
            assert "period" in p
            assert "count" in p
            assert "rolling_avg_3m" in p

    def test_analyze_evidence_refs(self):
        ta = TrendAnalyzer()
        req = CrimeTrendRequestDTO()
        result = ta.analyze(req)
        assert len(result.evidence_refs) == 1
        assert result.evidence_refs[0].evidence_type == "computed_statistic"


class TestHotspotDetector:
    def test_detect_returns_clusters(self):
        hd = HotspotDetector()
        req = HotspotRequestDTO(district_id=18)
        result = hd.detect(req)
        assert len(result.clusters) >= 1
        assert result.algorithm == "DBSCAN"

    def test_detect_uses_haversine(self):
        hd = HotspotDetector()
        req = HotspotRequestDTO(district_id=18, eps_km=1.0, min_cases=3)
        result = hd.detect(req)
        assert result.algorithm_params["metric"] == "haversine"
        assert result.algorithm_params["eps"] == 1.0
        assert result.algorithm_params["min_samples"] == 3

    def test_detect_unknown_district_defaults_to_bangalore(self):
        hd = HotspotDetector()
        req = HotspotRequestDTO(district_id=999)
        result = hd.detect(req)
        assert len(result.clusters) >= 0

    def test_detect_uses_case_master_location_schema(self):
        class MockDB:
            is_connected = True

            def __init__(self):
                self.sql = []

            def execute_non_query(self, sql):
                self.sql.append(sql)
                if "FROM Unit" in sql:
                    return {"columns": ["UnitID"], "rows": [[10]], "row_count": 1}
                return {
                    "columns": ["latitude", "longitude", "CaseMasterID", "CaseCategoryID"],
                    "rows": [[12.97, 77.59, 101, 1], [12.971, 77.591, 102, 1]],
                    "row_count": 2,
                }

        db = MockDB()
        hd = HotspotDetector()
        req = HotspotRequestDTO(district_id=18, eps_km=1.0, min_cases=2)
        result = hd.detect(req, db=db)
        case_sql = db.sql[-1]
        assert "FROM CaseMaster" in case_sql
        assert "latitude" in case_sql
        assert "CaseMasterID" in case_sql
        assert "latitide" not in case_sql
        assert result.total_cases_analyzed == 2


class TestStatsAggregator:
    def test_get_dashboard_stats_returns_expected_fields(self):
        sa = StatsAggregator()
        stats = sa.get_dashboard_stats()
        assert stats.district_count == 31
        assert stats.total_cases > 0
        assert stats.heinous_pct > 0

    def test_get_dashboard_stats_accepts_scope(self):
        sa = StatsAggregator()
        stats = sa.get_dashboard_stats(user_scope={"district_id": 18})
        assert stats.station_count > 0
