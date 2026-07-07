from functions.forecast.alert_engine import AlertEngine


class ScheduledAlertJob:
    def __init__(self):
        self.engine = AlertEngine()

    def run(self):
        alerts = self.engine.evaluate()
        for alert in alerts:
            print(f"[ScheduledAlert] {alert.alert_type}: {alert.title}")
        return alerts
