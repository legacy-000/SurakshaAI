"""Catalyst cron: triggers daily analytics via suraksha_ai API Gateway."""
import json, logging, traceback, urllib.request
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
_API_URL = "https://surakshaai-60076341598.development.catalystserverless.in/api/"

def handler(event, context):
    try:
        body = json.dumps({"action": "run_analytics"}).encode()
        req = urllib.request.Request(_API_URL, data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
        logger.info("analytics run complete: %s", result)
        context.close_with_success()
    except Exception as exc:
        logger.error("analytics cron failed: %s\n%s", exc, traceback.format_exc())
        context.close_with_failure()
