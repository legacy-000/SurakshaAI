import logging
import time
import uuid

logger = logging.getLogger(__name__)


class DatastoreNotConnectedError(Exception):
    pass


class DatastoreClient:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app

    @property
    def is_connected(self):
        return self._catalyst_app is not None

    def execute_query(self, sql_text: str, max_rows: int = 1000, timeout: int = 30) -> dict:
        query_id = str(uuid.uuid4())
        start = time.time()

        if not sql_text:
            return {"error": "DB_EMPTY_QUERY", "message": "Empty SQL query", "query_id": query_id}

        if not self.is_connected:
            try:
                from common.main_handler import _init_error
            except Exception:
                _init_error = "Could not import main_handler"
            return {
                "error": "DB_NOT_CONNECTED",
                "message": f"Catalyst DataStore is not connected. SDK Init Error: {_init_error}",
                "query_id": query_id,
                "execution_status": "failed",
                "execution_time_ms": 0,
            }

        return self._real_query(sql_text, query_id, start)

    def _real_query(self, sql_text: str, query_id: str, start: float) -> dict:
        try:
            zcql = self._catalyst_app.zcql()
            raw = zcql.execute_query(sql_text)

            if not raw or not isinstance(raw, list):
                rows, columns = [], []
            else:
                columns = list(raw[0].keys()) if raw else []
                rows = [[row.get(col) for col in columns] for row in raw]

            elapsed = int((time.time() - start) * 1000)
            return {
                "query_id": query_id,
                "execution_status": "success",
                "execution_time_ms": elapsed,
                "row_count": len(rows),
                "columns": columns,
                "rows": rows,
            }

        except Exception as e:
            logger.error("ZCQL query failed: %s", e)
            try:
                tables = self._catalyst_app.datastore().get_all_tables()
                table_names = [t.table_name if hasattr(t, "table_name") else (t.get("table_name") if isinstance(t, dict) else str(t)) for t in tables]
            except Exception as e2:
                table_names = f"Failed to get tables: {e2}"
            elapsed = int((time.time() - start) * 1000)
            return {
                "error": "DB_QUERY_FAILED",
                "message": f"{str(e)} | Available tables: {table_names}",
                "query_id": query_id,
                "execution_status": "failed",
                "execution_time_ms": elapsed,
            }
