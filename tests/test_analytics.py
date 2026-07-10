from functions.analytics.trend_analyzer import TrendAnalyzer
from functions.analytics.hotspot_detector import HotspotDetector
from functions.analytics.sociological_analyzer import SociologicalAnalyzer
from models.dto import CrimeTrendRequestDTO, HotspotRequestDTO, SociologicalAnalysisRequestDTO

def test_trend_analyzer():
    analyzer = TrendAnalyzer()
    req = CrimeTrendRequestDTO(dimension="month", group_by="district")
    result = analyzer.analyze(req)
    assert len(result.aggregation) > 0

def test_hotspot_detector():
    detector = HotspotDetector()
    req = HotspotRequestDTO(district_id=18)
    result = detector.detect(req)
    assert result.algorithm == "DBSCAN"

def test_sociological_analyzer():
    analyzer = SociologicalAnalyzer()
    req = SociologicalAnalysisRequestDTO(person_type="complainant")
    result = analyzer.analyze(req)
    assert result.sample_size > 0
