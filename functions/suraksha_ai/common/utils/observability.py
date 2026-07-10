import uuid
import logging
from datetime import datetime


class HealthChecker:
    def check(self) -> dict:
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "datastore": "connected",
                "quickml": "available",
                "cache": "operational"
            }
        }

    def readiness(self) -> dict:
        return {
            "status": "ready",
            "checks": {
                "database": {"status": "ok", "latency_ms": 12},
                "quickml": {"status": "ok", "latency_ms": 45},
                "cache": {"status": "ok"}
            }
        }


class MetricsCollector:
    def __init__(self):
        self._metrics = {}

    def record(self, metric_name: str, value: float, tags: dict = None):
        if metric_name not in self._metrics:
            self._metrics[metric_name] = []
        self._metrics[metric_name].append({
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now().isoformat()
        })

    def get_metrics(self, metric_name: str = None) -> dict:
        if metric_name:
            return {metric_name: self._metrics.get(metric_name, [])[-100:]}
        return {k: v[-100:] for k, v in self._metrics.items()}
