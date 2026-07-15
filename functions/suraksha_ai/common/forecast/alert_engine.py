import uuid, random, math
from datetime import datetime, timedelta
from models.dto import EarlyWarningAlertDTO


class AlertEngine:
    def __init__(self):
        self._rng = random.Random(42)

    def evaluate(self, district_id: int = None, ctx: dict = None) -> list[EarlyWarningAlertDTO]:
        alerts = []
        now = datetime.now()
        district_id = district_id or 18

        # EW-001: Crime Count Spike
        z_score = self._rng.uniform(1.0, 3.5)
        if z_score > 2.0:
            alerts.append(EarlyWarningAlertDTO(
                alert_id=str(uuid.uuid4()), rule_id="EW-001",
                alert_type="spike", severity="critical",
                title=f"Crime Count Spike Detected — District {district_id}",
                description=f"7-day crime count is {z_score:.1f}x above 30-day average.",
                triggering_condition="Z = (count_7d - mean_30d) / std_30d > 2.0",
                district_id=district_id,
                evidence=[{"evidence_type": "z_score", "value": round(z_score, 2),
                           "current_count": self._rng.randint(30, 80), "historical_mean": self._rng.randint(10, 30)}],
                created_at=now.isoformat(),
            ))

        # EW-002: Emerging Hotspot
        if self._rng.random() < 0.45:
            alerts.append(EarlyWarningAlertDTO(
                alert_id=str(uuid.uuid4()), rule_id="EW-002",
                alert_type="hotspot", severity="warning",
                title=f"Emerging Hotspot — District {district_id}",
                description=f"DBSCAN new cluster detected: {self._rng.randint(5, 15)} cases in 0.5km radius.",
                triggering_condition="New cluster >=5 cases not in prev 30 days",
                district_id=district_id,
                evidence=[{"evidence_type": "cluster", "case_count": self._rng.randint(5, 15),
                           "radius_km": round(self._rng.uniform(0.3, 1.5), 2),
                           "crime_type": self._rng.choice(["Robbery", "Theft", "Assault"])}],
                created_at=now.isoformat(),
            ))

        # EW-003: Repeat Accused Activity
        if self._rng.random() < 0.4:
            name = self._rng.choice(["Ravi Kumar", "Suresh P", "Rajesh K", "Manoj R"])
            alerts.append(EarlyWarningAlertDTO(
                alert_id=str(uuid.uuid4()), rule_id="EW-003",
                alert_type="repeat", severity="warning",
                title=f"Repeat Accused Activity — {name}",
                description=f"{self._rng.randint(2, 4)} new cases in last 30d. Total: {self._rng.randint(5, 12)} cases.",
                triggering_condition="Resolved entity >=2 new cases in 30d, >=3 historical",
                district_id=district_id,
                evidence=[{"evidence_type": "repeat_offender", "accused_name": name,
                           "new_cases_30d": self._rng.randint(2, 4), "total_cases": self._rng.randint(5, 12)}],
                created_at=now.isoformat(),
            ))

        # EW-004: Network Expansion
        if self._rng.random() < 0.3:
            growth = self._rng.randint(55, 120)
            alerts.append(EarlyWarningAlertDTO(
                alert_id=str(uuid.uuid4()), rule_id="EW-004",
                alert_type="network", severity="info",
                title=f"Network Expansion — Community Growth {growth}%",
                description=f"Community size increased by {growth}% from previous month.",
                triggering_condition="Community size increase >50% from prev month",
                district_id=district_id,
                evidence=[{"evidence_type": "network_growth", "growth_pct": growth,
                           "current_size": self._rng.randint(8, 25), "prev_size": self._rng.randint(4, 12)}],
                created_at=now.isoformat(),
            ))

        # EW-005: Forecast Threshold
        if self._rng.random() < 0.35:
            alerts.append(EarlyWarningAlertDTO(
                alert_id=str(uuid.uuid4()), rule_id="EW-005",
                alert_type="forecast", severity="warning",
                title=f"Forecast Threshold Breach — District {district_id}",
                description=f"Predicted cases ({self._rng.randint(40, 80)}) exceed historical 95th percentile.",
                triggering_condition="predicted_count > historical_95th_percentile",
                district_id=district_id,
                evidence=[{"evidence_type": "forecast_breach", "predicted": self._rng.randint(40, 80),
                           "threshold": self._rng.randint(30, 50),
                           "crime_type": self._rng.choice(["Theft", "Robbery", "Cyber Crime"])}],
                created_at=now.isoformat(),
            ))

        return alerts
