import uuid
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from models.dto import UserContextDTO

logger = logging.getLogger(__name__)


class Commander:
    def __init__(self, evidence_validator=None, max_workers: int = 4):
        self._agents = {}
        self._validator = evidence_validator
        self._max_workers = max_workers

    def register_agent(self, name: str, agent):
        self._agents[name] = agent

    def analyze_intent(self, query: str) -> dict:
        ql = query.lower()
        intents = []
        if any(w in ql for w in ["case", "fir", "crime", "accused", "victim"]):
            intents.append("database_query")
        if any(w in ql for w in ["trend", "increase", "decrease", "pattern", "month", "year"]):
            intents.append("trend_analysis")
        if any(w in ql for w in ["hotspot", "map", "area", "location", "district", "cluster"]):
            intents.append("geospatial_analysis")
        if any(w in ql for w in ["profile", "offender", "repeat", "history", "record"]):
            intents.append("offender_profile")
        if any(w in ql for w in ["predict", "forecast", "future", "next month", "expected"]):
            intents.append("forecast")
        if any(w in ql for w in ["network", "connection", "link", "relation", "gang"]):
            intents.append("network_analysis")
        if any(w in ql for w in ["alert", "warning", "spike", "anomaly"]):
            intents.append("alert_evaluation")
        if not intents:
            intents.append("database_query")
        return {"primary_intent": intents[0], "secondary_intents": intents[1:], "confidence": 0.85}

    def build_mission(self, query: str, intents: dict, user: UserContextDTO) -> dict:
        mission_id = str(uuid.uuid4())
        tasks = []
        # DAG: all tasks are independent → flat parallel fan-out
        all_intents = [intents["primary_intent"]] + intents["secondary_intents"][:2]
        for intent in all_intents:
            tasks.append({
                "task_id": str(uuid.uuid4()), "agent": intent,
                "query": query, "status": "pending",
                "result": None, "evidence": [], "depends_on": [],
            })
        return {"mission_id": mission_id, "query": query, "tasks": tasks,
                "user_id": user.user_id, "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "planned"}

    def _run_task(self, task: dict) -> dict:
        agent_name = task["agent"]
        agent = self._agents.get(agent_name)
        if not agent:
            task["status"] = "failed"
            task["result"] = f"No agent for intent: {agent_name}"
            return task
        try:
            task["status"] = "running"
            result = agent.run(task["query"])
            task["result"] = result.get("data")
            raw = result.get("evidence", [])
            task["evidence"] = self._validator.validate(raw) if self._validator else raw
            task["status"] = "completed"
        except Exception as e:
            logger.exception("Agent %s failed", agent_name)
            task["status"] = "failed"
            task["result"] = str(e)
        return task

    def execute_mission(self, mission: dict) -> dict:
        tasks = mission["tasks"]
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_map = {executor.submit(self._run_task, t): t for t in tasks}
            for future in as_completed(future_map):
                future.result()  # task is updated in-place via _run_task
        mission["status"] = "completed"
        return mission

    def run(self, query: str, user: UserContextDTO) -> dict:
        intents = self.analyze_intent(query)
        mission = self.build_mission(query, intents, user)
        mission = self.execute_mission(mission)
        summary = self._summarize(mission)
        return {"mission_id": mission["mission_id"], "intents": intents,
                "tasks": mission["tasks"], "summary": summary,
                "status": mission["status"]}

    def _summarize(self, mission: dict) -> str:
        completed = sum(1 for t in mission["tasks"] if t["status"] == "completed")
        failed = sum(1 for t in mission["tasks"] if t["status"] == "failed")
        total = len(mission["tasks"])
        return f"Mission complete: {completed}/{total} tasks succeeded, {failed} failed."
