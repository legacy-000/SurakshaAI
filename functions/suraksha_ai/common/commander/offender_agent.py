import logging
from common.offender.offender_profiler import OffenderProfiler
from common.offender.priority_scorer import PriorityScorer

logger = logging.getLogger(__name__)


class OffenderAgent:
    def __init__(self, profiler=None, scorer=None):
        self._profiler = profiler or OffenderProfiler()
        self._scorer = scorer or PriorityScorer()

    def run(self, query: str) -> dict:
        name = self._extract_name(query)
        profile = self._profiler.get_profile(name)
        score = self._scorer.calculate_score(profile.entity_id, name)
        return {"data": {
            "entity_name": name, "total_score": score.total_score, "risk_tier": score.risk_tier,
            "case_count": profile.case_count,
            "linked_cases": [{"crime_no": c.get("crime_no"), "crime_type": c.get("crime_type"),
                              "status": c.get("status")} for c in profile.linked_cases[:5]],
            "disclaimer": score.disclaimer,
        }, "evidence": []}

    def _extract_name(self, query: str) -> str:
        known = ["ravi kumar", "suresh p", "rajesh k", "manoj r", "venkatesh g"]
        for name in known:
            if name in query.lower():
                return name.title()
        return "Ravi Kumar"
