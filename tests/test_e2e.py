from functions.auth.auth_handler import AuthHandler
from functions.chat.chat_handler import ChatHandler
from functions.network.entity_resolver import EntityResolver
from functions.offender.priority_scorer import PriorityScorer
from functions.analytics.trend_analyzer import TrendAnalyzer
from functions.forecast.forecaster import Forecaster
from functions.analytics.hotspot_detector import HotspotDetector
from models.dto import LoginRequestDTO, QueryRequestDTO, EntityResolutionRequestDTO, \
    CrimeTrendRequestDTO, ForecastRequestDTO, HotspotRequestDTO, UserContextDTO

def test_full_investigator_journey():
    auth = AuthHandler()
    login = auth.login(LoginRequestDTO(kgid="INV001", password="test"))
    assert "token" in login

    user = UserContextDTO(**login["user"])
    handler = ChatHandler()
    req = QueryRequestDTO(message="Theft cases in Bangalore this year")
    resp = handler.handle_query(req, user)
    assert resp.content_text is not None

    resolver = EntityResolver()
    ent_req = EntityResolutionRequestDTO(accused_name="Ravi Kumar")
    ent_resp = resolver.resolve(ent_req)
    assert len(ent_resp.candidates) > 0

    scorer = PriorityScorer()
    score = scorer.calculate_score("ent_test", "Ravi Kumar")
    assert score.risk_tier in ["LOW", "MODERATE", "ELEVATED", "HIGH"]

def test_analyst_journey():
    trend = TrendAnalyzer()
    t_req = CrimeTrendRequestDTO(dimension="month", group_by="district")
    t_resp = trend.analyze(t_req)
    assert t_resp.total_records_analyzed > 0

    hotspot = HotspotDetector()
    h_req = HotspotRequestDTO(district_id=18)
    h_resp = hotspot.detect(h_req)
    assert h_resp.algorithm == "DBSCAN"

    forecast = Forecaster()
    f_req = ForecastRequestDTO(district_id=18, crime_sub_head_id=10)
    f_resp = forecast.forecast(f_req)
    assert f_resp.metrics["mae"] > 0
