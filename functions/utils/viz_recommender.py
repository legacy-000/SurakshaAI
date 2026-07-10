class VizRecommender:
    def recommend(self, exec_result: dict) -> str:
        row_count = exec_result.get("row_count", 0)
        columns = exec_result.get("columns", [])

        if row_count == 0:
            return None
        if "count" in columns and row_count <= 20:
            return "bar_chart"
        if "latitude" in columns or "longitude" in columns:
            return "map"
        if row_count > 1 and len(columns) >= 2:
            return "line_chart"
        return "table"
