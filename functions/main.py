"""Suraksha AI - Main Catalyst Serverless Function Entry Point."""

from functions.auth.auth_handler import AuthHandler
from functions.chat.chat_handler import ChatHandler
from functions.chat.voice_handler import VoiceHandler
from functions.chat.pdf_exporter import PDFExporter
from functions.analytics.trend_analyzer import TrendAnalyzer
from functions.analytics.hotspot_detector import HotspotDetector
from functions.analytics.sociological_analyzer import SociologicalAnalyzer
from functions.analytics.stats_aggregator import StatsAggregator
from functions.analytics.report_generator import ReportGenerator
from functions.network.entity_resolver import EntityResolver
from functions.network.graph_projector import GraphProjector
from functions.network.graph_analyzer import GraphAnalyzer
from functions.network.community_detector import CommunityDetector
from functions.offender.offender_profiler import OffenderProfiler
from functions.offender.priority_scorer import PriorityScorer
from functions.investigation.investigation_manager import InvestigationManager
from functions.investigation.similarity_engine import SimilarityEngine
from functions.investigation.timeline_generator import TimelineGenerator
from functions.investigation.lead_generator import LeadGenerator
from functions.investigation.financial_stub import FinancialStub
from functions.forecast.forecaster import Forecaster
from functions.forecast.alert_engine import AlertEngine
from functions.evidence.evidence_builder import EvidenceBuilder
from functions.security.audit_logger import AuditLogger
from functions.security.injection_detector import InjectionDetector
from functions.cache.cache_manager import CacheManager
from functions.ai.case_summarizer import CaseSummarizer
from functions.health.health_handler import HealthHandler
from functions.auth.rbac_middleware import RBACMiddleware

from models.dto import (
    LoginRequestDTO, QueryRequestDTO, UserContextDTO,
    CrimeTrendRequestDTO, HotspotRequestDTO,
    SociologicalAnalysisRequestDTO, EntityResolutionRequestDTO,
    ForecastRequestDTO, FeedbackDTO
)


class SurakshaAIHandler:
    def __init__(self):
        self.auth = AuthHandler()
        self.chat = ChatHandler()
        self.voice = VoiceHandler()
        self.pdf = PDFExporter()
        self.trends = TrendAnalyzer()
        self.hotspots = HotspotDetector()
        self.sociological = SociologicalAnalyzer()
        self.stats = StatsAggregator()
        self.reports = ReportGenerator()
        self.entity_resolver = EntityResolver()
        self.graph_projector = GraphProjector()
        self.graph_analyzer = GraphAnalyzer()
        self.community_detector = CommunityDetector()
        self.offender_profiler = OffenderProfiler()
        self.priority_scorer = PriorityScorer()
        self.investigations = InvestigationManager()
        self.similarity = SimilarityEngine()
        self.timeline = TimelineGenerator()
        self.leads = LeadGenerator()
        self.financial = FinancialStub()
        self.forecaster = Forecaster()
        self.alerts = AlertEngine()
        self.evidence = EvidenceBuilder()
        self.audit = AuditLogger()
        self.injection = InjectionDetector()
        self.cache = CacheManager()
        self.summarizer = CaseSummarizer()
        self.health = HealthHandler()
        self.rbac = RBACMiddleware()


handler = SurakshaAIHandler()


def auth_login(request):
    req = LoginRequestDTO(**request)
    return handler.auth.login(req)


def chat_query(request, user_context=None):
    req = QueryRequestDTO(**request)
    return handler.chat.handle_query(req, user_context)


def get_trends(params, user_context=None):
    req = CrimeTrendRequestDTO(**params)
    return handler.trends.analyze(req)


def get_hotspots(params, user_context=None):
    req = HotspotRequestDTO(**params)
    return handler.hotspots.detect(req)


def get_sociological(params, user_context=None):
    req = SociologicalAnalysisRequestDTO(**params)
    return handler.sociological.analyze(req)


def get_network_search(body, user_context=None):
    return handler.graph_projector.build_graph(
        body.get("accused_name", ""),
        body.get("depth", 2)
    )


def get_offender_profile(name, user_context=None):
    return handler.offender_profiler.get_profile(name)


def get_priority_score(entity_id, entity_name, user_context=None):
    return handler.priority_scorer.calculate_score(entity_id, entity_name)


def get_forecast(params, user_context=None):
    req = ForecastRequestDTO(**params)
    return handler.forecaster.forecast(req)


def get_alerts(params, user_context=None):
    return handler.alerts.evaluate()


def get_financial_status(user_context=None):
    return handler.financial.get_status()


def get_health():
    return handler.health.handle_health()


def get_ready():
    return handler.health.handle_readiness()
