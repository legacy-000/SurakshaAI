from datetime import datetime


class HealthHandler:
    def __init__(self, db_connected: bool = False):
        self._db_connected = db_connected

    def check_readiness(self) -> dict:
        return {"status": "ok", "db_connected": self._db_connected, "timestamp": datetime.now().isoformat()}

    def check_liveness(self) -> dict:
        return {"status": "alive"}
