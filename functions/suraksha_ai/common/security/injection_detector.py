import re


class InjectionDetector:
    SQL_PATTERNS = [
        r"'.*OR.*'='", r"'.*--", r"DROP\s+TABLE", r"UNION\s+SELECT",
        r"DELETE\s+FROM", r"INSERT\s+INTO", r"UPDATE\s+.*SET",
        r"EXEC", r"xp_cmdshell", r"INTO\s+OUTFILE",
        r"pg_sleep", r"WAITFOR\s+DELAY", r"BENCHMARK\("
    ]

    PROMPT_PATTERNS = [
        r"ignore.*(?:previous|above|instruction)", r"forget.*(?:all|context)",
        r"you are.*(?:now|instead)", r"system.*prompt", r"override",
        r"disregard", r"bypass", r"jailbreak"
    ]

    def detect_sql_injection(self, input_text: str) -> bool:
        upper = input_text.upper()
        for pattern in self.SQL_PATTERNS:
            if re.search(pattern, upper):
                return True
        return False

    def detect_prompt_injection(self, input_text: str) -> bool:
        lower = input_text.lower()
        for pattern in self.PROMPT_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False

    def sanitize(self, input_text: str) -> str:
        sanitized = input_text
        sanitized = re.sub(r"['\";\\]", "", sanitized)
        return sanitized
