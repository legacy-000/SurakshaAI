from models.dto import HealthCheckDTO
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class TestHealthHandler:
    def test_health_dto_returns_healthy_by_default(self):
        h = HealthCheckDTO()
        assert h.status == "healthy"
        assert h.version is not None

    def test_health_dto_can_set_custom_status(self):
        h = HealthCheckDTO(status="degraded")
        assert h.status == "degraded"
