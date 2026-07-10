import random
from datetime import datetime, timedelta
from common.models.dto import CrimeTrendRequestDTO, CrimeTrendResultDTO, EvidenceReferenceDTO


class TrendAnalyzer:
    def analyze(self, req: CrimeTrendRequestDTO) -> CrimeTrendResultDTO:
        periods = []
        base_count = random.randint(100, 500)
        now = datetime.now()

        for i in range(12):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1
            count = base_count + random.randint(-50, 50)
            pct = round((count - base_count) / base_count * 100, 1) if i > 0 else None
            periods.append({
                "period": f"{year}-{month:02d}",
                "count": count,
                "pct_change": pct,
                "rolling_avg_3m": round((count + base_count + base_count) / 3)
            })
            base_count = count

        return CrimeTrendResultDTO(
            query_id="trend_mock_id",
            aggregation=periods,
            total_records_analyzed=sum(p["count"] for p in periods),
            evidence_refs=[EvidenceReferenceDTO(
                evidence_id="ev_trend_1",
                evidence_type="computed_statistic",
                source_table="CaseMaster",
                display_label=f"Trend analysis over {len(periods)} periods"
            )]
        )
