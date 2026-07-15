import uuid
from datetime import datetime
from typing import Optional

from models.dto import (
    EvidenceReferenceDTO,
    ModelRegistryEntryDTO,
    PromptRegistryEntryDTO,
    AgentCapabilityDTO,
    AgentExecutionDTO,
    AgentResultEnvelopeDTO,
    MissionDTO,
    MissionTaskDTO,
    ClaimLedgerEntryDTO,
)


class ModelRegistry:
    def __init__(self):
        self._models = {}

    def register(self, model_name: str, model_version: str, provider: str = "",
                 capabilities: list[str] = None, parameters: dict = None) -> ModelRegistryEntryDTO:
        entry = ModelRegistryEntryDTO(
            model_id=str(uuid.uuid4()),
            model_name=model_name, model_version=model_version,
            provider=provider, capabilities=capabilities or [],
            parameters=parameters or {},
            created_at=datetime.now().isoformat(),
        )
        self._models[entry.model_id] = entry
        return entry

    def get(self, model_id: str) -> Optional[ModelRegistryEntryDTO]:
        return self._models.get(model_id)

    def list_all(self) -> list[ModelRegistryEntryDTO]:
        return list(self._models.values())


class PromptRegistry:
    def __init__(self):
        self._prompts = {}

    def register(self, prompt_name: str, prompt_version: str, prompt_text: str,
                 model_id: str = None) -> PromptRegistryEntryDTO:
        entry = PromptRegistryEntryDTO(
            prompt_id=str(uuid.uuid4()),
            prompt_name=prompt_name, prompt_version=prompt_version,
            prompt_text=prompt_text, model_id=model_id,
            created_at=datetime.now().isoformat(),
        )
        self._prompts[entry.prompt_id] = entry
        return entry

    def get(self, prompt_id: str) -> Optional[PromptRegistryEntryDTO]:
        return self._prompts.get(prompt_id)

    def list_all(self) -> list[PromptRegistryEntryDTO]:
        return list(self._prompts.values())


class AgentCapabilityRegistry:
    def __init__(self):
        self._agents = {}

    def register(self, agent_name: str, intents: list[str], description: str = "",
                 required_permissions: list[str] = None) -> AgentCapabilityDTO:
        dto = AgentCapabilityDTO(
            agent_name=agent_name, intents=intents, description=description,
            required_permissions=required_permissions or [],
        )
        self._agents[agent_name] = dto
        return dto

    def get(self, agent_name: str) -> Optional[AgentCapabilityDTO]:
        return self._agents.get(agent_name)

    def list_all(self) -> list[AgentCapabilityDTO]:
        return list(self._agents.values())


class AgentExecutionTracker:
    def __init__(self):
        self._executions = {}

    def start(self, mission_id: str, agent_name: str, intent: str = "",
              input_query: str = "") -> AgentExecutionDTO:
        exec_ = AgentExecutionDTO(
            execution_id=str(uuid.uuid4()),
            mission_id=mission_id, agent_name=agent_name,
            intent=intent, input_query=input_query,
            status="running",
            started_at=datetime.now().isoformat(),
        )
        self._executions[exec_.execution_id] = exec_
        return exec_

    def complete(self, execution_id: str, output_summary: str = "",
                 evidence_ids: list[str] = None) -> bool:
        exec_ = self._executions.get(execution_id)
        if not exec_:
            return False
        exec_.output_summary = output_summary
        exec_.evidence_ids = evidence_ids or []
        exec_.status = "completed"
        exec_.completed_at = datetime.now().isoformat()
        return True

    def fail(self, execution_id: str, error: str = "") -> bool:
        exec_ = self._executions.get(execution_id)
        if not exec_:
            return False
        exec_.status = "failed"
        exec_.completed_at = datetime.now().isoformat()
        return True

    def get(self, execution_id: str) -> Optional[AgentExecutionDTO]:
        return self._executions.get(execution_id)

    def list_by_mission(self, mission_id: str) -> list[AgentExecutionDTO]:
        return [e for e in self._executions.values() if e.mission_id == mission_id]

    def envelope(self, execution_id: str, data: any = None,
                 evidence: list[EvidenceReferenceDTO] = None,
                 error: str = None, duration_ms: int = None) -> AgentResultEnvelopeDTO:
        exec_ = self._executions.get(execution_id)
        return AgentResultEnvelopeDTO(
            execution_id=execution_id,
            agent_name=exec_.agent_name if exec_ else "",
            status=exec_.status if exec_ else "unknown",
            data=data, evidence=evidence or [],
            error=error, duration_ms=duration_ms,
        )


class MissionTracker:
    def __init__(self, execution_tracker: AgentExecutionTracker):
        self._missions = {}
        self._tasks = {}
        self._executions = execution_tracker

    def create(self, query: str, user_id: str = "",
               intents: dict = None) -> MissionDTO:
        mission = MissionDTO(
            mission_id=str(uuid.uuid4()),
            query=query, user_id=user_id,
            intents=intents or {}, status="created",
            created_at=datetime.now().isoformat(),
        )
        self._missions[mission.mission_id] = mission
        return mission

    def add_task(self, mission_id: str, agent_name: str, intent: str = "",
                 input_query: str = "") -> Optional[MissionTaskDTO]:
        if mission_id not in self._missions:
            return None
        task = MissionTaskDTO(
            task_id=str(uuid.uuid4()),
            mission_id=mission_id, agent_name=agent_name,
            intent=intent, input_query=input_query,
            status="pending",
        )
        self._tasks[task.task_id] = task
        return task

    def start_task(self, task_id: str) -> Optional[MissionTaskDTO]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = "running"
        task.started_at = datetime.now().isoformat()
        return task

    def complete_task(self, task_id: str, result: any = None,
                      evidence: list[EvidenceReferenceDTO] = None) -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = "completed"
        task.result = result
        task.evidence = evidence or []
        task.completed_at = datetime.now().isoformat()
        return True

    def fail_task(self, task_id: str, error: str = "") -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = "failed"
        task.error = error
        task.completed_at = datetime.now().isoformat()
        return True

    def get_mission(self, mission_id: str) -> Optional[MissionDTO]:
        return self._missions.get(mission_id)

    def get_task(self, task_id: str) -> Optional[MissionTaskDTO]:
        return self._tasks.get(task_id)

    def list_missions(self) -> list[MissionDTO]:
        return list(self._missions.values())

    def list_tasks(self, mission_id: str) -> list[MissionTaskDTO]:
        return [t for t in self._tasks.values() if t.mission_id == mission_id]

    def update_mission_status(self, mission_id: str, status: str,
                              summary: str = "") -> bool:
        mission = self._missions.get(mission_id)
        if not mission:
            return False
        mission.status = status
        mission.summary = summary or mission.summary
        if status in ("completed", "failed"):
            mission.completed_at = datetime.now().isoformat()
        return True


class ClaimLedger:
    def __init__(self):
        self._claims = {}

    def add_entry(self, statement: str, classification: str, producer: str,
                  model_version: str = None, evidence_refs: list[str] = None,
                  confidence: float = 1.0, source_execution_id: str = None) -> ClaimLedgerEntryDTO:
        entry = ClaimLedgerEntryDTO(
            claim_id=str(uuid.uuid4()),
            statement=statement, classification=classification,
            producer=producer, model_version=model_version,
            evidence_refs=evidence_refs or [],
            confidence=confidence,
            confidence_label="high" if confidence >= 0.8 else "medium" if confidence >= 0.5 else "low",
            created_at=datetime.now().isoformat(),
            source_execution_id=source_execution_id,
        )
        self._claims[entry.claim_id] = entry
        return entry

    def update_status(self, claim_id: str, status: str) -> bool:
        entry = self._claims.get(claim_id)
        if not entry:
            return False
        entry.validation_status = status
        return True

    def get(self, claim_id: str) -> Optional[ClaimLedgerEntryDTO]:
        return self._claims.get(claim_id)

    def list_all(self) -> list[ClaimLedgerEntryDTO]:
        return list(self._claims.values())
