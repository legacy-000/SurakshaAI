import logging
import time
import uuid

logger = logging.getLogger(__name__)


class DatastoreNotConnectedError(Exception):
    pass


class DatastoreClient:
    def __init__(self, catalyst_app=None):
        if catalyst_app is not None:
            self._catalyst_app = catalyst_app
        else:
            try:
                import zcatalyst_sdk
                self._catalyst_app = zcatalyst_sdk.initialize()
            except Exception as e:
                logger.info("Catalyst SDK not auto-initialized (expected in local tests): %s", e)
                self._catalyst_app = None

    @property
    def is_connected(self):
        return self._catalyst_app is not None

    def test_connection(self) -> dict:
        if not self.is_connected:
            return {"status": "disconnected", "error": "SDK not initialized"}
        try:
            start = time.time()
            tables = self._catalyst_app.datastore().get_all_tables()
            elapsed = int((time.time() - start) * 1000)
            return {
                "status": "connected",
                "latency_ms": elapsed,
                "table_count": len(tables)
            }
        except Exception as e:
            return {"status": "disconnected", "error": str(e)}

    def execute_query(self, sql_text: str, max_rows: int = 1000, timeout: int = 30) -> dict:
        query_id = str(uuid.uuid4())
        start = time.time()

        if not sql_text:
            return {"error": "DB_EMPTY_QUERY", "message": "Empty SQL query", "query_id": query_id}

        if not self.is_connected:
            return {
                "error": "DB_NOT_CONNECTED",
                "message": "Catalyst SDK not connected or initialized. Database access unavailable.",
                "query_id": query_id,
                "execution_status": "failed",
                "execution_time_ms": int((time.time() - start) * 1000)
            }

        return self._real_query(sql_text, query_id, start)

    def _real_query(self, sql_text: str, query_id: str, start: float) -> dict:
        try:
            zcql = self._catalyst_app.zcql()
            raw = zcql.execute_query(sql_text)

            if not raw or not isinstance(raw, list):
                rows, columns = [], []
            else:
                first_row = raw[0]
                is_nested = any(isinstance(val, dict) for val in first_row.values())

                if is_nested:
                    columns = []
                    for table_name, columns_dict in first_row.items():
                        if isinstance(columns_dict, dict):
                            for col_name in columns_dict.keys():
                                columns.append(f"{table_name}.{col_name}")
                        else:
                            columns.append(table_name)
                    
                    rows = []
                    for row in raw:
                        row_vals = []
                        for table_name, columns_dict in row.items():
                            if isinstance(columns_dict, dict):
                                for col_val in columns_dict.values():
                                    row_vals.append(col_val)
                            else:
                                row_vals.append(columns_dict)
                        rows.append(row_vals)
                else:
                    columns = list(first_row.keys())
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

    def insert_row(self, table_name: str, row_data: dict) -> dict:
        if not self.is_connected:
            return {"error": "DB_NOT_CONNECTED", "message": "Database not connected"}
        try:
            table = self._catalyst_app.datastore().table(table_name)
            res = table.insert_row(row_data)
            # Handle both Zoho Catalyst row object and dictionary return types
            if hasattr(res, 'get_row_details'):
                res_data = res.get_row_details()
            elif isinstance(res, dict):
                res_data = res
            else:
                res_data = {"inserted_row": str(res)}
            return {"status": "success", "data": res_data}
        except Exception as e:
            logger.error("Failed to insert row in %s: %s", table_name, e)
            return {"error": "DB_INSERT_FAILED", "message": str(e)}

