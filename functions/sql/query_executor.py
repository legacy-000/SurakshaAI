import uuid
import time
import random


class QueryExecutor:
    def __init__(self):
        self._mock_data = self._build_mock_data()

    def execute(self, sql_text: str, max_rows: int = 1000, timeout: int = 30) -> dict:
        query_id = str(uuid.uuid4())
        start = time.time()

        if not sql_text or "SELECT" not in sql_text.upper():
            return {"error": "DB_TIMEOUT_001", "message": "Invalid query", "query_id": query_id}

        time.sleep(random.uniform(0.05, 0.2))

        result = self._mock_query(sql_text)
        elapsed = int((time.time() - start) * 1000)

        result["query_id"] = query_id
        result["execution_time_ms"] = elapsed
        result["execution_status"] = "success"
        return result

    def _mock_query(self, sql_text: str) -> dict:
        sql_upper = sql_text.upper()
        columns = ["count"] if "COUNT" in sql_upper else ["CaseMasterID", "CrimeNo", "Status"]

        if "ACCUSED" in sql_upper and "NAME" in sql_upper:
            return {
                "row_count": 3, "columns": ["AccusedMasterID", "AccusedName", "CaseMasterID"],
                "rows": [[1, "Ravi Kumar", 101], [2, "Suresh P", 102], [3, "Rajesh K", 101]]
            }
        if "COUNT" in sql_upper:
            return {
                "row_count": 1, "columns": ["count"],
                "rows": [[random.randint(10, 3000)]]
            }
        if "GROUP BY" in sql_upper or "group by" in sql_text.lower():
            return {
                "row_count": 5, "columns": ["group_key", "count"],
                "rows": [["Bangalore", 1200], ["Mysuru", 450], ["Hubli", 230], ["Mangalore", 310], ["Belgaum", 180]]
            }
        return {
            "row_count": random.randint(5, 50), "columns": columns,
            "rows": [[i, f"CN2024{i:04d}", "Under Investigation"] for i in range(1, random.randint(5, 20))]
        }

    def _build_mock_data(self):
        pass
