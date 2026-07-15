import logging

from common.auth.auth_handler import AuthHandler
from common.chat.chat_handler import ChatHandler
from common.analytics.trend_analyzer import TrendAnalyzer
from common.analytics.hotspot_detector import HotspotDetector
from common.analytics.stats_aggregator import StatsAggregator
from common.network.graph_projector import GraphProjector
from common.offender.offender_profiler import OffenderProfiler
from common.offender.priority_scorer import PriorityScorer
from common.forecast.forecaster import Forecaster
from common.forecast.alert_engine import AlertEngine
from common.db.datastore_client import DatastoreClient
from common.security.rbac_middleware import RBACMiddleware
from common.security.audit_logger import AuditLogger
from common.ai.quickml_client import QuickMLClient
from common.commander.commander import Commander
from common.commander.database_agent import DatabaseAgent
from common.commander.trend_agent import TrendAgent
from common.commander.geospatial_agent import GeospatialAgent
from common.commander.offender_agent import OffenderAgent
from common.commander.evidence_validator import EvidenceValidator
from common.investigation.investigation_manager import InvestigationManager
from common.investigation.similarity_engine import SimilarityEngine
from common.investigation.timeline_generator import TimelineGenerator
from common.investigation.lead_generator import LeadGenerator
from common.investigation.report_generator import ReportGenerator as InvReportGenerator
from common.governance.governance import (
    ModelRegistry, PromptRegistry, AgentCapabilityRegistry,
    AgentExecutionTracker, MissionTracker, ClaimLedger,
)
from common.comms.message_engine import MessageEngine
from common.comms.permission_engine import PermissionEngine
from common.comms.group_manager import GroupManager
from common.support.tse_handler import TSEHandler

logger = logging.getLogger(__name__)


class SurakshaAIHandler:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app
        self._db_client = DatastoreClient(self._catalyst_app)
        self.quickml = QuickMLClient(self._catalyst_app)

        self.auth = AuthHandler(self._catalyst_app)
        self.chat = ChatHandler(self._catalyst_app)
        self.trends = TrendAnalyzer()
        self.hotspots = HotspotDetector()
        self.stats = StatsAggregator()
        self.graph_projector = GraphProjector()
        self.offender_profiler = OffenderProfiler()
        self.priority_scorer = PriorityScorer()
        self.forecaster = Forecaster()
        self.alerts = AlertEngine()
        self.rbac = RBACMiddleware(self._db_client)
        self.audit = AuditLogger(self._db_client)
        self.evidence_validator = EvidenceValidator()

        # Investigation Suite
        self.investigations = InvestigationManager()
        self.similarity = SimilarityEngine(self.quickml, self._db_client)
        self.timeline = TimelineGenerator()
        self.leads = LeadGenerator()
        self.inv_reports = InvReportGenerator()

        # AI Governance — Phase 5
        self.model_registry = ModelRegistry()
        self.prompt_registry = PromptRegistry()
        self.agent_capabilities = AgentCapabilityRegistry()
        self.execution_tracker = AgentExecutionTracker()
        self.mission_tracker = MissionTracker(self.execution_tracker)
        self.claim_ledger = ClaimLedger()

        # Communication & Resource Sharing
        self.messages = MessageEngine(self._db_client)
        self.permissions = PermissionEngine(self._db_client)
        self.groups = GroupManager(self._db_client)

        # Technical Support Engineer — diagnostics
        self.tse = TSEHandler(self._db_client, self._catalyst_app)

        # Commander + agents
        self.commander = Commander(self.evidence_validator)
        self.commander.register_agent("database_query", DatabaseAgent(self.chat, self._db_client))
        self.commander.register_agent("trend_analysis", TrendAgent(self.trends))
        self.commander.register_agent("geospatial_analysis", GeospatialAgent(self.hotspots))
        self.commander.register_agent("offender_profile", OffenderAgent(self.offender_profiler, self.priority_scorer))

        # Seed governance registries with known agents
        self.agent_capabilities.register("database_query", ["database_query", "case_lookup", "evidence_search"],
                                          "Query the FIR database for case details, offender records, and evidence.", ["chat_query"])
        self.agent_capabilities.register("trend_analysis", ["trend_analysis", "pattern_analysis"],
                                          "Analyze crime trends and detect patterns over time.", ["view_trends"])
        self.agent_capabilities.register("geospatial_analysis", ["geospatial_analysis", "hotspot_detection"],
                                          "Detect crime hotspots and analyze geographic crime patterns.", ["view_geospatial"])
        self.agent_capabilities.register("offender_profile", ["offender_profile", "priority_scoring"],
                                          "Build offender profiles and compute priority risk scores.", ["view_offender"])

    @property
    def is_live(self):
        return self._catalyst_app is not None
