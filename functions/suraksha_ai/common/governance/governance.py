import json
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

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

if TYPE_CHECKING:
    from db.datastore_client import DatastoreClient  # noqa: F401

logger = logging.getLogger(__name__)

# ponytail: tolerate unprovisioned table on cold start.
# Every DB call is best-effort: if the Catalyst Data Store is not connected
# (tests / local dev) or a Gov* table is not yet provisioned, writes log and
# move on, reads return an empty set. The in-memory dict is the source of
# truth for the running instance; the DB row is a durable append-only mirror
# hydrated on next cold start. Latest ROWID wins per logical key.


def _shared_db() -> "DatastoreClient":
    # Lazy import avoids a circular dependency with main_handler.
    from db.datastore_client import DatastoreClient
    return DatastoreClient()


def _db_ok(res: dict) -> bool:
    return isinstance(res, dict) and "error" not in res


def _table_missing(res: dict, table: str) -> bool:
    if not isinstance(res, dict):
        return False
    if "error" not in res:
        return False
    # ponytail: tolerate unprovisioned table on cold start.
    # ZCQL surfaces a missing table as DB_EXEC_FAILED with a message
    # referencing the table name. We must not treat connection loss as empty.
    if res.get("error") == "DB_NOT_CONNECTED":
        return False
    msg = str(res.get("message", "")).lower()
    return table.lower() in msg or "does not exist" in msg or "table" in msg


def _hydrate_rows(db, table: str, where_col: Optional[str] = None,
                  where_val: Optional[str] = None) -> list[dict]:
    """Read rows from DB; return list of dicts. Empty if table missing or DB off."""
    sql = f"SELECT * FROM {table}"
    if where_col is not None and where_val is not None:
        esc = str(where_val).replace("'", "''")
        sql += f" WHERE {where_col} = '{esc}'"
    sql += " LIMIT 300"  # ponytail: ZCQL LIMIT-only pagination; MAX_LIMIT=300
    res = db.execute_non_query(sql)
    if not _db_ok(res):
        if _table_missing(res, table):
            logger.debug("Table %s not provisioned; treating as empty", table)
        return []
    cols = res.get("columns", []) or []
    rows = res.get("rows", []) or []
    out = []
    for r in rows:
        if len(r) != len(cols):
            continue
        out.append(dict(zip(cols, r)))
    return out


def _insert_row(db, table: str, row: dict) -> None:
    """Best-effort INSERT; logs and moves on if DB unavailable."""
    res = db.insert_bulk_rows(table, [row])
    if not _db_ok(res):
        logger.debug("Insert into %s skipped: %s", table, res)


def _latest_by_key(rows: list[dict], key_col: str) -> dict:
    """Given rows with ROWID, return the row with the highest ROWID per key_col.

    Used on cold-start hydrate where state changes were appended over time.
    Falls back to the first row if ROWID is not present.
    """
    if not rows:
        return {}
    best: dict = {}
    best_rowid: dict = {}
    for r in rows:
        k = r.get(key_col)
        if k is None:
            continue
        rid = r.get("ROWID") or r.get("rowid")
        if rid is None:
            best.setdefault(k, r)
            continue
        if k not in best_rowid or rid > best_rowid[k]:
            best_rowid[k] = rid
            best[k] = r
    return best


# ── ModelRegistry ─────────────────────────────────────────────────────

class ModelRegistry:
    def __init__(self, db=None):
        self._db = db or _shared_db()
        self._models: dict[str, ModelRegistryEntryDTO] = {}
        self._hydrate()

    def _hydrate(self):
        rows = _hydrate_rows(self._db, "GovModel")
        for r in _latest_by_key(rows, "ModelId").values():
            entry = ModelRegistryEntryDTO(
                model_id=r.get("ModelId", ""),
                model_name=r.get("ModelName", ""),
                model_version=r.get("ModelVersion", ""),
                provider=r.get("Provider", "") or "",
                capabilities=json.loads(r.get("CapabilitiesJson") or "[]"),
                parameters=json.loads(r.get("ParametersJson") or "{}"),
                created_at=r.get("RegisteredAt", "") or "",
            )
            if entry.model_id:
                self._models[entry.model_id] = entry

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
        # ponytail: persist write before returning.
        _insert_row(self._db, "GovModel", {
            "ModelId": entry.model_id,
            "ModelName": entry.model_name,
            "ModelVersion": entry.model_version,
            "Provider": entry.provider or None,
            "CapabilitiesJson": json.dumps(entry.capabilities),
            "ParametersJson": json.dumps(entry.parameters),
            "RegisteredAt": entry.created_at,
        })
        return entry

    def get(self, model_id: str) -> Optional[ModelRegistryEntryDTO]:
        return self._models.get(model_id)

    def list_all(self) -> list[ModelRegistryEntryDTO]:
        return list(self._models.values())


# ── PromptRegistry ─────────────────────────────────────────────────────

class PromptRegistry:
    def __init__(self, db=None):
        self._db = db or _shared_db()
        self._prompts: dict[str, PromptRegistryEntryDTO] = {}
        self._hydrate()

    def _hydrate(self):
        rows = _hydrate_rows(self._db, "GovPrompt")
        for r in _latest_by_key(rows, "PromptId").values():
            entry = PromptRegistryEntryDTO(
                prompt_id=r.get("PromptId", ""),
                prompt_name=r.get("PromptName", ""),
                prompt_version=r.get("PromptVersion", ""),
                prompt_text=r.get("Template", "") or "",
                model_id=r.get("ModelId"),
                created_at=r.get("CreatedAt", "") or "",
            )
            if entry.prompt_id:
                self._prompts[entry.prompt_id] = entry

    def register(self, prompt_name: str, prompt_version: str, prompt_text: str,
                 model_id: str = None) -> PromptRegistryEntryDTO:
        entry = PromptRegistryEntryDTO(
            prompt_id=str(uuid.uuid4()),
            prompt_name=prompt_name, prompt_version=prompt_version,
            prompt_text=prompt_text, model_id=model_id,
            created_at=datetime.now().isoformat(),
        )
        self._prompts[entry.prompt_id] = entry
        # ponytail: persist write before returning.
        _insert_row(self._db, "GovPrompt", {
            "PromptId": entry.prompt_id,
            "PromptName": entry.prompt_name,
            "PromptVersion": entry.prompt_version,
            "Template": entry.prompt_text,
            "ModelId": entry.model_id,
            "CreatedAt": entry.created_at,
        })
        return entry

    def get(self, prompt_id: str) -> Optional[PromptRegistryEntryDTO]:
        return self._prompts.get(prompt_id)

    def list_all(self) -> list[PromptRegistryEntryDTO]:
        return list(self._prompts.values())


# ── AgentCapabilityRegistry ───────────────────────────────────────────

class AgentCapabilityRegistry:
    def __init__(self, db=None):
        self._db = db or _shared_db()
        self._agents: dict[str, AgentCapabilityDTO] = {}
        self._hydrate()

    def _hydrate(self):
        rows = _hydrate_rows(self._db, "GovAgentCapability")
        for r in _latest_by_key(rows, "AgentName").values():
            dto = AgentCapabilityDTO(
                agent_name=r.get("AgentName", ""),
                intents=json.loads(r.get("CapabilitiesJson") or "[]"),
                description=r.get("Description", "") or "",
                required_permissions=json.loads(r.get("RequiredPermissionsJson") or "[]"),
            )
            if dto.agent_name:
                self._agents[dto.agent_name] = dto

    def register(self, agent_name: str, intents: list[str], description: str = "",
                 required_permissions: list[str] = None) -> AgentCapabilityDTO:
        dto = AgentCapabilityDTO(
            agent_name=agent_name, intents=intents, description=description,
            required_permissions=required_permissions or [],
        )
        self._agents[agent_name] = dto
        # ponytail: persist write before returning.
        _insert_row(self._db, "GovAgentCapability", {
            "AgentName": dto.agent_name,
            "CapabilitiesJson": json.dumps(dto.intents),
            "Description": dto.description or None,
            "RequiredPermissionsJson": json.dumps(dto.required_permissions),
            "UpdatedAt": datetime.now().isoformat(),
        })
        return dto

    def get(self, agent_name: str) -> Optional[AgentCapabilityDTO]:
        return self._agents.get(agent_name)

    def list_all(self) -> list[AgentCapabilityDTO]:
        return list(self._agents.values())


# ── AgentExecutionTracker ─────────────────────────────────────────────

class AgentExecutionTracker:
    def __init__(self, db=None):
        self._db = db or _shared_db()
        self._executions: dict[str, AgentExecutionDTO] = {}
        self._hydrate()

    def _hydrate(self):
        rows = _hydrate_rows(self._db, "GovExecution")
        for r in _latest_by_key(rows, "ExecutionId").values():
            dto = AgentExecutionDTO(
                execution_id=r.get("ExecutionId", ""),
                mission_id=r.get("MissionId", "") or "",
                agent_name=r.get("AgentName", "") or "",
                intent=r.get("Intent", "") or "",
                input_query=r.get("InputQuery", "") or "",
                output_summary=r.get("OutputSummary", "") or "",
                evidence_ids=json.loads(r.get("EvidenceIdsJson") or "[]"),
                status=r.get("Status", "running") or "running",
                started_at=r.get("StartedAt", "") or "",
                completed_at=r.get("CompletedAt"),
            )
            if dto.execution_id:
                self._executions[dto.execution_id] = dto

    def _persist(self, e: AgentExecutionDTO) -> None:
        # ponytail: append a fresh row on every state change; latest ROWID wins on hydrate.
        _insert_row(self._db, "GovExecution", {
            "ExecutionId": e.execution_id,
            "MissionId": e.mission_id,
            "AgentName": e.agent_name,
            "Intent": e.intent or None,
            "InputQuery": e.input_query or None,
            "StartedAt": e.started_at or None,
            "CompletedAt": e.completed_at,
            "Status": e.status,
            "OutputSummary": e.output_summary or None,
            "EvidenceIdsJson": json.dumps(list(e.evidence_ids)),
            "Error": None,
        })

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
        # ponytail: persist write before returning.
        self._persist(exec_)
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
        # ponytail: persist write before returning.
        self._persist(exec_)
        return True

    def fail(self, execution_id: str, error: str = "") -> bool:
        exec_ = self._executions.get(execution_id)
        if not exec_:
            return False
        exec_.status = "failed"
        exec_.completed_at = datetime.now().isoformat()
        # ponytail: persist write before returning. (error kept in OutputSummary
        # as AgentExecutionDTO has no error field)
        if error:
            exec_.output_summary = exec_.output_summary or error
        self._persist(exec_)
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


# ── MissionTracker ───────────────────────────────────────────────────

class MissionTracker:
    def __init__(self, execution_tracker: AgentExecutionTracker, db=None):
        self._db = db or _shared_db()
        self._missions: dict[str, MissionDTO] = {}
        self._tasks: dict[str, MissionTaskDTO] = {}
        self._executions = execution_tracker
        self._hydrate()

    def _hydrate(self):
        # Missions
        for r in _latest_by_key(_hydrate_rows(self._db, "GovMission"), "MissionId").values():
            dto = MissionDTO(
                mission_id=r.get("MissionId", ""),
                query=r.get("Query", "") or "",
                user_id=r.get("UserId", "") or "",
                intents=json.loads(r.get("IntentsJson") or "{}"),
                status=r.get("Status", "created") or "created",
                summary=r.get("Summary", "") or "",
                created_at=r.get("CreatedAt", "") or "",
                completed_at=r.get("CompletedAt"),
            )
            if dto.mission_id:
                self._missions[dto.mission_id] = dto
        # Tasks (GovMissionTask)
        for r in _latest_by_key(_hydrate_rows(self._db, "GovMissionTask"), "TaskId").values():
            dto = MissionTaskDTO(
                task_id=r.get("TaskId", ""),
                mission_id=r.get("MissionId", "") or "",
                agent_name=r.get("AgentName", "") or "",
                intent=r.get("Intent", "") or "",
                input_query=r.get("InputQuery", "") or "",
                status=r.get("Status", "pending") or "pending",
                result=json.loads(r.get("ResultJson") or "null"),
                evidence=[EvidenceReferenceDTO(**ev) for ev in json.loads(r.get("EvidenceJson") or "[]")],
                started_at=r.get("StartedAt", "") or "",
                completed_at=r.get("CompletedAt"),
                error=r.get("Error"),
            )
            if dto.task_id:
                self._tasks[dto.task_id] = dto

    def _persist_mission(self, m: MissionDTO) -> None:
        # ponytail: append a fresh row on state change; latest ROWID wins on hydrate.
        _insert_row(self._db, "GovMission", {
            "MissionId": m.mission_id,
            "Query": m.query or None,
            "UserId": m.user_id or None,
            "IntentsJson": json.dumps(m.intents),
            "Status": m.status,
            "Summary": m.summary or None,
            "CreatedAt": m.created_at or None,
            "CompletedAt": m.completed_at,
            "DetailsJson": "{}",
        })

    def _persist_task(self, t: MissionTaskDTO) -> None:
        _insert_row(self._db, "GovMissionTask", {
            "TaskId": t.task_id,
            "MissionId": t.mission_id,
            "AgentName": t.agent_name,
            "Intent": t.intent or None,
            "InputQuery": t.input_query or None,
            "Status": t.status,
            "StartedAt": t.started_at or None,
            "CompletedAt": t.completed_at,
            "ResultJson": json.dumps(t.result) if t.result is not None else None,
            "EvidenceJson": json.dumps([e.model_dump() for e in t.evidence]),
            "Error": t.error,
        })

    def create(self, query: str, user_id: str = "",
               intents: dict = None) -> MissionDTO:
        mission = MissionDTO(
            mission_id=str(uuid.uuid4()),
            query=query, user_id=user_id,
            intents=intents or {}, status="created",
            created_at=datetime.now().isoformat(),
        )
        self._missions[mission.mission_id] = mission
        # ponytail: persist write before returning.
        self._persist_mission(mission)
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
        # ponytail: persist write before returning.
        self._persist_task(task)
        return task

    def start_task(self, task_id: str) -> Optional[MissionTaskDTO]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = "running"
        task.started_at = datetime.now().isoformat()
        # ponytail: persist write before returning.
        self._persist_task(task)
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
        # ponytail: persist write before returning.
        self._persist_task(task)
        return True

    def fail_task(self, task_id: str, error: str = "") -> bool:
        task = self._tasks.get(task_id)
        if not task:
            return False
        task.status = "failed"
        task.error = error
        task.completed_at = datetime.now().isoformat()
        # ponytail: persist write before returning.
        self._persist_task(task)
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
        # ponytail: persist write before returning.
        self._persist_mission(mission)
        return True


# ── ClaimLedger ───────────────────────────────────────────────────────

class ClaimLedger:
    def __init__(self, db=None):
        self._db = db or _shared_db()
        self._claims: dict[str, ClaimLedgerEntryDTO] = {}
        self._hydrate()

    def _hydrate(self):
        for r in _latest_by_key(_hydrate_rows(self._db, "GovClaim"), "ClaimId").values():
            dto = ClaimLedgerEntryDTO(
                claim_id=r.get("ClaimId", ""),
                statement=r.get("Statement", "") or "",
                classification=r.get("Classification", "DATABASE_FACT") or "DATABASE_FACT",
                producer=r.get("Producer", "") or "",
                model_version=r.get("ModelVersion"),
                evidence_refs=json.loads(r.get("EvidenceRefsJson") or "[]"),
                confidence=float(r.get("Confidence") or 1.0),
                confidence_label=r.get("ConfidenceLabel", "high") or "high",
                validation_status=r.get("ValidationStatus", "Under Review") or "Under Review",
                created_at=r.get("GrantedAt", "") or "",
                source_execution_id=r.get("SourceExecutionId"),
            )
            if dto.claim_id:
                self._claims[dto.claim_id] = dto

    def _persist(self, e: ClaimLedgerEntryDTO) -> None:
        # ponytail: append a fresh row on state change; latest ROWID wins on hydrate.
        _insert_row(self._db, "GovClaim", {
            "ClaimId": e.claim_id,
            "Statement": e.statement or None,
            "Classification": e.classification or None,
            "Producer": e.producer or None,
            "ModelVersion": e.model_version,
            "EvidenceRefsJson": json.dumps(list(e.evidence_refs)),
            "Confidence": e.confidence,
            "ConfidenceLabel": e.confidence_label,
            "ValidationStatus": e.validation_status,
            "GrantedAt": e.created_at or None,
            "ExpiresAt": None,
            "Status": e.validation_status,
            "SourceExecutionId": e.source_execution_id,
            "ClaimMetadataJson": "{}",
        })

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
        # ponytail: persist write before returning.
        self._persist(entry)
        return entry

    def update_status(self, claim_id: str, status: str) -> bool:
        entry = self._claims.get(claim_id)
        if not entry:
            return False
        entry.validation_status = status
        # ponytail: persist write before returning.
        self._persist(entry)
        return True

    def get(self, claim_id: str) -> Optional[ClaimLedgerEntryDTO]:
        return self._claims.get(claim_id)

    def list_all(self) -> list[ClaimLedgerEntryDTO]:
        return list(self._claims.values())
