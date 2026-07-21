import logging

logger = logging.getLogger(__name__)


class DatastoreClient:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app
        if catalyst_app is None:
            try:
                import zcatalyst_sdk
                self._catalyst_app = zcatalyst_sdk.initialize()
            except Exception as e:
                logger.info("Catalyst SDK not auto-initialized: %s", e)

    @property
    def is_connected(self):
        return self._catalyst_app is not None

    def execute_non_query(self, sql: str) -> dict:
        if not self.is_connected:
            return {"error": "DB_NOT_CONNECTED", "message": "Database not connected"}
        try:
            raw = self._catalyst_app.zcql().execute_query(sql)
            if not raw:
                return {"status": "success", "row_count": 0, "columns": [], "rows": [], "response": str(raw)}
            cols = []
            if isinstance(raw[0], dict):
                for td in raw[0].values():
                    cols.extend(td.keys())
            rows = []
            for r in raw:
                vals = []
                if isinstance(r, dict):
                    for td in r.values():
                        vals.extend(td.values())
                rows.append(vals)
            return {"status": "success", "row_count": len(rows), "columns": cols, "rows": rows, "response": str(raw)}
        except Exception as e:
            logger.error("ZCQL execute failed: %s", e)
            return {"error": "DB_EXEC_FAILED", "message": str(e)}

    def insert_bulk_rows(self, table_name: str, rows: list) -> dict:
        if not self.is_connected:
            return {"error": "DB_NOT_CONNECTED", "message": "Database not connected"}
        try:
            count = 0
            for row in rows:
                cols = ", ".join(row.keys())
                vals = []
                for v in row.values():
                    if v is None:
                        vals.append("NULL")
                    elif isinstance(v, bool):
                        vals.append("true" if v else "false")
                    elif isinstance(v, (int, float)):
                        vals.append(str(v))
                    else:
                        vals.append(f"'{str(v).replace(chr(39), chr(39)+chr(39))}'")
                res = self.execute_non_query(f"INSERT INTO {table_name} ({cols}) VALUES ({', '.join(vals)})")
                if "error" in res:
                    return {"error": "DB_BULK_INSERT_FAILED", "message": res.get(
                        "message", ""), "sql": f"INSERT INTO {table_name} ({cols}) VALUES (...)"}
                count += 1
            return {"status": "success", "inserted": count}
        except Exception as e:
            logger.error("Bulk insert failed for %s: %s", table_name, e)
            return {"error": "DB_BULK_INSERT_FAILED", "message": str(e)}
