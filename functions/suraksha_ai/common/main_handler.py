"""Suraksha AI - Main Catalyst Serverless Function Entry Point."""

import logging

from common.auth.auth_handler import AuthHandler
from common.chat.chat_handler import ChatHandler
from common.chat.voice_handler import VoiceHandler
from common.chat.pdf_exporter import PDFExporter
from common.analytics.trend_analyzer import TrendAnalyzer
from common.analytics.hotspot_detector import HotspotDetector
from common.analytics.sociological_analyzer import SociologicalAnalyzer
from common.analytics.stats_aggregator import StatsAggregator
from common.analytics.report_generator import ReportGenerator
from common.network.entity_resolver import EntityResolver
from common.network.graph_projector import GraphProjector
from common.network.graph_analyzer import GraphAnalyzer
from common.network.community_detector import CommunityDetector
from common.offender.offender_profiler import OffenderProfiler
from common.offender.priority_scorer import PriorityScorer
from common.investigation.investigation_manager import InvestigationManager
from common.investigation.similarity_engine import SimilarityEngine
from common.investigation.timeline_generator import TimelineGenerator
from common.investigation.lead_generator import LeadGenerator
from common.investigation.financial_stub import FinancialStub
from common.forecast.forecaster import Forecaster
from common.forecast.alert_engine import AlertEngine
from common.evidence.evidence_builder import EvidenceBuilder
from common.security.audit_logger import AuditLogger
from common.security.injection_detector import InjectionDetector
from common.cache.cache_manager import CacheManager
from common.ai.case_summarizer import CaseSummarizer
from common.health.health_handler import HealthHandler
from common.auth.rbac_middleware import RBACMiddleware
from common.db.datastore_client import DatastoreClient

from common.models.dto import (
    LoginRequestDTO, QueryRequestDTO, UserContextDTO,
    CrimeTrendRequestDTO, HotspotRequestDTO,
    SociologicalAnalysisRequestDTO, EntityResolutionRequestDTO,
    ForecastRequestDTO, FeedbackDTO
)

logger = logging.getLogger(__name__)


_init_error = None


def _init_catalyst_app():
    global _init_error
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        logger.info("Catalyst SDK initialized successfully")
        return app
    except Exception as e:
        _init_error = f"{type(e).__name__}: {str(e)}"
        logger.error("Catalyst SDK not available: %s", e)
        return None


class SurakshaAIHandler:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app or _init_catalyst_app()

        self.auth = AuthHandler()
        self.chat = ChatHandler(self._catalyst_app)
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

    @property
    def is_live(self):
        return self._catalyst_app is not None


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
