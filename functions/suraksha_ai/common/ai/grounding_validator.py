import re


class GroundingValidator:
    def validate(self, answer: str, result: dict) -> str:
        if result.get("error"):
            return "unverified"
        if not answer or not result.get("row_count", 0):
            return "partial"
        row_count = result["row_count"]
        count_pattern = re.search(r"(\d[\d,]*)\s* cases|\b(\d+)\s* records|\bfound\s+(\d+)", answer, re.I)
        if count_pattern:
            extracted = next(g for g in count_pattern.groups() if g is not None)
            if extracted and int(extracted.replace(",", "")) != row_count:
                return "partial"
        return "verified"
