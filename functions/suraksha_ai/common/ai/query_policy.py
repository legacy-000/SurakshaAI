MAX_ROWS = 1000
MAX_WHERE_CLAUSES = 10
MAX_IN_VALUES = 500
DEFAULT_TIMEOUT_S = 30


class QueryPolicy:
    def __init__(self):
        self.max_rows = MAX_ROWS
        self.max_where_clauses = MAX_WHERE_CLAUSES
        self.max_in_values = MAX_IN_VALUES
        self.timeout_s = DEFAULT_TIMEOUT_S

    def enforce(self, params: dict) -> list[str]:
        warnings = []

        limit = params.get("limit", 50)
        if limit and limit > self.max_rows:
            warnings.append(f"limit capped to {self.max_rows} (requested {limit})")

        where = params.get("where", [])
        if where and len(where) > self.max_where_clauses:
            warnings.append(f"WHERE clauses capped to {self.max_where_clauses} (requested {len(where)})")

        if where:
            for cond in where:
                if cond.get("operator") == "IN" and isinstance(cond.get("value"), list):
                    if len(cond["value"]) > self.max_in_values:
                        warnings.append(f"IN list truncated to {self.max_in_values} values")

        return warnings


class UsageTracker:
    def __init__(self):
        self._call_count = 0

    def track(self, params: dict):
        self._call_count += 1

    @property
    def total_calls(self) -> int:
        return self._call_count
