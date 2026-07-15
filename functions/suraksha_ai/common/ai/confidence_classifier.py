class ConfidenceClassifier:
    def classify(self, result: dict) -> str:
        if result.get("error"):
            return "insufficient_data"
        row_count = result.get("row_count", 0)
        quality_warnings = result.get("quality_warnings", [])
        if result.get("source") == "regex_fallback":
            return "medium" if row_count > 0 else "low"
        if row_count == 0:
            return "low" if quality_warnings else "medium"
        if len(quality_warnings) > 2:
            return "medium"
        return "high"
