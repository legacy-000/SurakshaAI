import logging
from datetime import datetime
from common.models.dto import CrimeTrendRequestDTO, EvidenceReferenceDTO

logger = logging.getLogger(__name__)


class TrendAgent:
    def __init__(self, trend_analyzer=None):
        self._analyzer = trend_analyzer

    def run(self, query: str) -> dict:
        if self._analyzer:
            req = CrimeTrendRequestDTO(crime_sub_head_id=1)
            result = self._analyzer.analyze(req)
            periods = [{"period": p["period"], "count": p["count"], "pct_change": p["pct_change"]}
                       for p in result.aggregation[:12]]
            evidence = [e.model_dump() for e in result.evidence_refs] if result.evidence_refs else []
            return {"data": {"aggregation": periods, "total": result.total_records_analyzed}, "evidence": evidence}
        return {"data": {"aggregation": [], "note": f"Trend analysis mock: {query}"}, "evidence": []}
