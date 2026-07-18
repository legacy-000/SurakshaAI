import json
import uuid
import logging
from datetime import datetime
from models.dto import InvestigationDTO, SavedGraphDTO

logger = logging.getLogger(__name__)

# ZCQL DDL (Catalyst Data Store) — provision once per environment. ROWID is the
# auto-increment PK; we keep InvestigationID as a unique business key.
# ponytail: tolerate unprovisioned table on cold start — SELECTs on a missing
# table return an error shape from DatastoreClient and we treat it as empty.
DDL = {
    "Investigation": (
        "CREATE TABLE IF NOT EXISTS Investigation ("
        "InvestigationID VARCHAR(64), "
        "Title VARCHAR(255), "
        "Description TEXT, "
        "OwnerKGID VARCHAR(64), "
        "Status VARCHAR(32), "
        "CreatedAt VARCHAR(40), "
        "UpdatedAt VARCHAR(40))"
    ),
    "InvestigationCase": (
        "CREATE TABLE IF NOT EXISTS InvestigationCase ("
        "InvestigationID VARCHAR(64), "
        "CaseMasterID INT, "
        "Notes TEXT, "
        "AddedAt VARCHAR(40))"
    ),
    "InvestigationQuery": (
        "CREATE TABLE IF NOT EXISTS InvestigationQuery ("
        "InvestigationID VARCHAR(64), "
        "QueryID VARCHAR(128), "
        "AddedAt VARCHAR(40))"
    ),
    "InvestigationGraph": (
        "CREATE TABLE IF NOT EXISTS InvestigationGraph ("
        "InvestigationID VARCHAR(64), "
        "SavedGraphID VARCHAR(64), "
        "Label VARCHAR(255), "
        "CenterNodeName VARCHAR(255), "
        "NodeCount INT, "
        "EdgeCount INT, "
        "CreatedAt VARCHAR(40), "
        "GraphJSON TEXT)"
    ),
}

_TABLE_MISSING_TOKENS = ("does not exist", "no such table", "not find", "unknown table")


class InvestigationManager:
    def __init__(self, db_client=None, catalyst_app=None):
        self._db = db_client
        if self._db is None and catalyst_app is not None:
            from db.datastore_client import DatastoreClient
            self._db = DatastoreClient(catalyst_app)
        self._investigations = {}
        self._ensured = False
        self._ensure_tables()
        self._load_from_db()

    # ── DB helpers ────────────────────────────────────────────────────
    def _ensure_tables(self):
        if self._db is None or not getattr(self._db, "is_connected", False):
            return
        if self._ensured:
            return
        self._ensured = True
        for ddl in DDL.values():
            try:
                self._db.execute_non_query(ddl)
            except Exception as e:
                logger.debug("DDL failed (likely tolerable): %s", e)

    @staticmethod
    def _is_table_missing(res: dict) -> bool:
        if not res or "error" not in res:
            return False
        msg = (res.get("message") or "") + " " + (res.get("response") or "")
        return any(tok in msg.lower() for tok in _TABLE_MISSING_TOKENS)

    @staticmethod
    def _q_sql_escape(v) -> str:
        if v is None:
            return "NULL"
        if isinstance(v, bool):
            return "true" if v else "false"
        if isinstance(v, (int, float)):
            return str(v)
        s = str(v).replace("'", "''")
        return f"'{s}'"

    def _insert(self, table: str, row: dict) -> dict:
        if self._db is None:
            return {"error": "DB_NOT_CONNECTED"}
        cols = ", ".join(row.keys())
        vals = ", ".join(self._q_sql_escape(v) for v in row.values())
        return self._db.execute_non_query(
            f"INSERT INTO {table} ({cols}) VALUES ({vals})"
        )

    def _delete_where(self, table: str, where: str) -> dict:
        if self._db is None:
            return {"error": "DB_NOT_CONNECTED"}
        return self._db.execute_non_query(f"DELETE FROM {table} WHERE {where}")

    def _select(self, sql: str) -> list:
        if self._db is None:
            return []
        res = self._db.execute_non_query(sql)
        if not res or "error" in res:
            # ponytail: tolerate unprovisioned table on cold start
            return []
        return res.get("rows", []) or []

    def _persist_ok(self, res: dict) -> bool:
        return bool(res) and res.get("status") == "success"

    # ── load ───────────────────────────────────────────────────────────
    def _load_from_db(self):
        if self._db is None or not getattr(self._db, "is_connected", False):
            return
        rows = self._select(
            "SELECT InvestigationID, Title, Description, OwnerKGID, Status, "
            "CreatedAt FROM Investigation"
        )
        if not rows:
            return
        for r in rows:
            inv_id, title, desc, _owner, status, created = (  # noqa: F841
                r[0], r[1], r[2], r[3], r[4], r[5]
            )
            if not inv_id:
                continue
            dto = InvestigationDTO(
                investigation_id=inv_id, title=title or "",
                description=desc or "", status=status or "open",
                created_at=created or "", case_count=0, query_count=0,
            )
            self._investigations[inv_id] = {
                "dto": dto, "cases": [], "queries": [], "graphs": []
            }
        # cases
        for r in self._select(
            "SELECT InvestigationID, CaseMasterID, Notes, AddedAt "
            "FROM InvestigationCase"
        ):
            rec = self._investigations.get(r[0])
            if rec:
                rec["cases"].append(
                    {"case_master_id": r[1], "notes": r[2] or ""}
                )
                rec["dto"].case_count = len(rec["cases"])
        # queries
        for r in self._select(
            "SELECT InvestigationID, QueryID, AddedAt "
            "FROM InvestigationQuery"
        ):
            rec = self._investigations.get(r[0])
            if rec:
                rec["queries"].append({"query_id": r[1]})
                rec["dto"].query_count = len(rec["queries"])
        # graphs
        for r in self._select(
            "SELECT InvestigationID, SavedGraphID, Label, CenterNodeName, "
            "NodeCount, EdgeCount, CreatedAt, GraphJSON FROM InvestigationGraph"
        ):
            rec = self._investigations.get(r[0])
            if rec:
                rec["graphs"].append(SavedGraphDTO(
                    saved_graph_id=r[1], label=r[2] or "",
                    center_node_name=r[3], node_count=r[4] or 0,
                    edge_count=r[5] or 0, created_at=r[6] or "",
                ))

    # ── public API (unchanged signatures) ─────────────────────────────
    def create(self, title: str, description: str = "", user_id: str = "") -> InvestigationDTO:
        inv = InvestigationDTO(
            investigation_id=str(uuid.uuid4()),
            title=title, description=description,
            status="open", created_at=datetime.now().isoformat(),
            case_count=0, query_count=0,
        )
        self._investigations[inv.investigation_id] = {
            "dto": inv, "cases": [], "queries": [], "graphs": []
        }
        res = self._insert("Investigation", {
            "InvestigationID": inv.investigation_id,
            "Title": inv.title,
            "Description": inv.description or "",
            "OwnerKGID": user_id or "",
            "Status": inv.status,
            "CreatedAt": inv.created_at,
            "UpdatedAt": inv.created_at,
        })
        if not self._persist_ok(res):
            logger.warning("Investigation insert failed: %s", res)
        return inv

    def get(self, investigation_id: str) -> dict:
        record = self._investigations.get(investigation_id)
        if not record:
            return None
        dto = record["dto"]
        return {"investigation_id": dto.investigation_id, "title": dto.title,
                "description": dto.description, "status": dto.status,
                "created_at": dto.created_at, "cases": record["cases"],
                "queries": record["queries"],
                "graphs": [g.model_dump() for g in record["graphs"]]}

    def list_all(self) -> list:
        return [self.get(i) for i in self._investigations]

    def _flush_required(self) -> bool:
        # Writes MUST hit the DB before reporting success — unless no DB is
        # connected at all (local test run / SDK not initialized), in which
        # case the in-memory record is the source of truth and we succeed so
        # callers don't break in environments without a Data Store.
        return self._db is not None and getattr(self._db, "is_connected", False)

    def _flush_ok(self, res: dict) -> bool:
        if not self._flush_required():
            return True
        return self._persist_ok(res)

    def add_case(self, investigation_id: str, case_master_id: int, notes: str = "") -> bool:
        record = self._investigations.get(investigation_id)
        if not record:
            return False
        record["cases"].append({"case_master_id": case_master_id, "notes": notes})
        dto = record["dto"]
        dto.case_count = len(record["cases"])
        res = self._insert("InvestigationCase", {
            "InvestigationID": investigation_id,
            "CaseMasterID": case_master_id,
            "Notes": notes or "",
            "AddedAt": datetime.now().isoformat(),
        })
        return self._flush_ok(res)

    def add_query(self, investigation_id: str, query_id: str) -> bool:
        record = self._investigations.get(investigation_id)
        if not record:
            return False
        record["queries"].append({"query_id": query_id})
        res = self._insert("InvestigationQuery", {
            "InvestigationID": investigation_id,
            "QueryID": query_id,
            "AddedAt": datetime.now().isoformat(),
        })
        return self._flush_ok(res)

    def add_graph(self, investigation_id: str, graph_data: dict, label: str) -> SavedGraphDTO:
        record = self._investigations.get(investigation_id)
        if not record:
            return None
        saved = SavedGraphDTO(
            saved_graph_id=str(uuid.uuid4()),
            label=label,
            node_count=len(graph_data.get("nodes", [])),
            edge_count=len(graph_data.get("edges", [])),
            created_at=datetime.now().isoformat()
        )
        record["graphs"].append(saved)
        res = self._insert("InvestigationGraph", {
            "InvestigationID": investigation_id,
            "SavedGraphID": saved.saved_graph_id,
            "Label": label or "",
            "CenterNodeName": "",
            "NodeCount": saved.node_count,
            "EdgeCount": saved.edge_count,
            "CreatedAt": saved.created_at,
            "GraphJSON": json.dumps(graph_data, default=str),
        })
        if not self._persist_ok(res):
            logger.warning("InvestigationGraph insert failed: %s", res)
        return saved
