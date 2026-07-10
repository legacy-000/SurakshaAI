import random
from common.models.dto import DashboardStatsDTO


class StatsAggregator:
    def get_dashboard_stats(self, user_scope: dict = None) -> DashboardStatsDTO:
        return DashboardStatsDTO(
            total_cases=random.randint(5000, 15000),
            heinous_pct=round(random.uniform(15, 35), 1),
            pending_cases=random.randint(500, 3000),
            district_count=31,
            station_count=random.randint(200, 400)
        )
