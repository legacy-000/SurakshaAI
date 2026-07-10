from common.utils.observability import HealthChecker


class HealthHandler:
    def __init__(self):
        self.checker = HealthChecker()

    def handle_health(self) -> dict:
        return self.checker.check()

    def handle_readiness(self) -> dict:
        return self.checker.readiness()
