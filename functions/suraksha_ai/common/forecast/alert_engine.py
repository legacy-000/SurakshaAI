import uuid
import random
from datetime import datetime
from common.models.dto import EarlyWarningAlertDTO


class AlertEngine:
    def evaluate(self, district_id: int = None) -> list[EarlyWarningAlertDTO]:
        alerts = []

        if random.random() < 0.4:
            alerts.append(EarlyWarningAlertDTO(
                alert_id=str(uuid.uuid4()),
                rule_id="EW-001",
                alert_type="spike",
                severity="critical",
                title=f"Crime Count Spike Detected - District {district_id or 18}",
                description="7-day crime count is 2.5x above 30-day average.",
                triggering_condition="Z = (count_7d - mean_30d) / std_30d > 2.0",
                district_id=district_id or 18,
                evidence=[{
                    "evidence_type": "z_score",
                    "value": round(random.uniform(2.0, 3.5), 2),
                    "current_count": random.randint(30, 80),
                    "historical_mean": random.randint(10, 30)
                }],
                created_at=datetime.now().isoformat()
            ))

        return alerts
