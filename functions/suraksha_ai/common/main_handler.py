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

logger = logging.getLogger(__name__)


class SurakshaAIHandler:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app
        self.auth = AuthHandler()
        self.chat = ChatHandler(self._catalyst_app)
        self.trends = TrendAnalyzer()
        self.hotspots = HotspotDetector()
        self.stats = StatsAggregator()
        self.graph_projector = GraphProjector()
        self.offender_profiler = OffenderProfiler()
        self.priority_scorer = PriorityScorer()
        self.forecaster = Forecaster()
        self.alerts = AlertEngine()
        self._db_client = DatastoreClient(self._catalyst_app)

    @property
    def is_live(self):
        return self._catalyst_app is not None
