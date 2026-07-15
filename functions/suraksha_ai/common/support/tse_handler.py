import logging

logger = logging.getLogger(__name__)


class TSEHandler:
    def __init__(self, db_client=None, catalyst_app=None):
        self._db = db_client
        self._catalyst_app = catalyst_app

    def schema_tables(self) -> dict:
        if self._catalyst_app:
            try:
                ds = self._catalyst_app.datastore()
                tbls = []
                for t in ds.get_all_tables():
                    d = t.to_dict() if hasattr(t, 'to_dict') else t
                    tbls.append(d.get("table_name", ""))
                return {"tables": sorted(tbls)}
            except Exception as e:
                logger.info("Live schema listing unavailable: %s", e)
        try:
            from ai.schema_registry import STATIC_SCHEMA
        except ImportError:
            from schema_registry import STATIC_SCHEMA  # noqa: F811
        return {"tables": sorted(STATIC_SCHEMA.keys()), "note": "static schema (not live)"}

    def schema_columns(self, table_name: str) -> dict:
        if self._catalyst_app:
            try:
                tbl = self._catalyst_app.datastore().table(table_name)
                cols = []
                for c in tbl.get_all_columns():
                    d = c.to_dict() if hasattr(c, 'to_dict') else c
                    cols.append({"name": d.get("column_name", ""), "type": d.get("column_type", "VARCHAR")})
                return {"table": table_name, "columns": cols}
            except Exception as e:
                return {"error": str(e)}
        try:
            from ai.schema_registry import STATIC_SCHEMA
        except ImportError:
            from schema_registry import STATIC_SCHEMA  # noqa: F811
        cols = [{"name": n, "type": v.get("type", "VARCHAR")} for n, v in STATIC_SCHEMA.get(table_name, {}).items()]
        return {"table": table_name, "columns": cols}

    def constraint_check(self) -> dict:
        if self._is_live():
            res = self._db.execute_non_query("SELECT table_name, constraint_name, constraint_type FROM information_schema.table_constraints WHERE constraint_type = 'FOREIGN KEY'")
            return {"constraints": res.get("rows", []), "status": "checked"}
        # mock check for dev
        return {"status": "ok", "constraints": [], "note": "mock (not live — no real constraint check)"}

    def system_metrics(self) -> dict:
        if self._is_live():
            try:
                res = self._db.execute_non_query("SELECT check_time, status_code, duration_ms FROM system_health ORDER BY check_time DESC LIMIT 10")
                return {"metrics": res.get("rows", [])}
            except Exception:
                pass
        return {"status": "unknown", "note": "mock metrics (not live — no system_health table)", "suggested_checks": ["CPU > 85%", "Disk > 90%", "Cache hit rate < 80%"]}

    def active_sessions(self) -> dict:
        if self._is_live():
            try:
                res = self._db.execute_non_query("SELECT pid, usename, application_name, state, query_start FROM pg_stat_activity WHERE state != 'idle'")
                return {"sessions": res.get("rows", [])}
            except Exception:
                pass
        return {"sessions": [{"pid": 12345, "usename": "suraksha_app", "application_name": "SurakshaAPI", "state": "active"}], "note": "mock session data (not live)"}

    def index_stats(self) -> dict:
        if self._is_live():
            try:
                res = self._db.execute_non_query("SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read FROM pg_stat_user_indexes ORDER BY idx_scan DESC LIMIT 20")
                return {"indexes": res.get("rows", [])}
            except Exception:
                pass
        return {"indexes": [], "note": "mock (not live — no pg_stat_user_indexes)"}

    def error_logs(self, limit: int = 20) -> dict:
        if self._is_live():
            try:
                sql = f"SELECT error_timestamp, error_code, stack_trace FROM system_logs WHERE log_level = 'ERROR' ORDER BY error_timestamp DESC LIMIT {min(limit, 100)}"
                res = self._db.execute_non_query(sql)
                return {"errors": res.get("rows", [])}
            except Exception:
                pass
        return {"errors": [{"error_timestamp": "2026-07-15T10:00:00Z", "error_code": "TSE_DIAG_001", "stack_trace": "Mock diagnostic: no live system_logs table"}], "note": "mock logs (not live)"}

    def cache_stats(self) -> dict:
        return {"cache_name": "default", "hit_rate": 0.92, "eviction_count": 12, "size_bytes": 1048576, "note": "mock stats (not live)"}

    def auth_tokens(self) -> dict:
        return {"tokens": [{"token_id": "tok_001", "token_issuer": "Catalyst", "issued_at": "2026-07-01T00:00:00Z", "expires_at": "2026-07-08T00:00:00Z", "status": "EXPIRED"}], "note": "mock tokens (not live)"}

    def validate_sql(self, sql: str) -> dict:
        st = sql.strip().upper()
        issues = []
        forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
        for kw in forbidden_keywords:
            if st.startswith(kw):
                issues.append(f"DDL/DML not allowed via diagnostic endpoint: {kw}")
        if " CASE " in st and "WHEN" in st:
            issues.append("CASE expressions may not render correctly in ZCQL")
        if " JOIN " in st:
            issues.append("JOINs not supported in ZCQL — use multi-step queries with IN")
        if " LIKE " in st:
            issues.append("LIKE operator not supported — use exact =")
        return {"sql": sql, "valid": len(issues) == 0, "issues": issues, "estimated_cost": "EXPLAIN unavailable in dev mode"}

    def _is_live(self):
        return self._db and self._db.is_connected
