class AnswerGenerator:
    def generate(self, exec_result: dict, original_query: str = "") -> str:
        row_count = exec_result.get("row_count", 0)
        if row_count == 0:
            return "No records found matching your query."

        columns = exec_result.get("columns", [])
        rows = exec_result.get("rows", [])

        if row_count == 1 and rows:
            parts = []
            for i, col in enumerate(columns):
                val = rows[0][i] if i < len(rows[0]) else ""
                parts.append(f"{col}: {val}")
            return "Found 1 record: " + ", ".join(parts)

        if len(columns) <= 3:
            summary = f"Found {row_count} records. "
            if rows and len(columns) >= 1:
                first_col = columns[0]
                unique_vals = len(set(str(r[0]) for r in rows if r))
                summary += f"Across {unique_vals} unique {first_col} values."
            return summary

        return f"Found {row_count} records matching your query."
