import uuid
import re
from datetime import datetime

from models.dto import (
    QueryRequestDTO, ConversationMessageDTO, EvidenceReferenceDTO
)
from common.sql.query_executor import QueryExecutor
from common.ai.answer_generator import AnswerGenerator


class InMemoryConversation:
    def __init__(self):
        self._store = {}
        self._ctx = {}

    def create_conversation(self, user_id, language_code="en"):
        cid = str(uuid.uuid4())
        self._store[cid] = {"user_id": user_id, "lang": language_code, "messages": []}
        return cid

    def get_context(self, cid, limit=10):
        conv = self._store.get(cid)
        return [] if not conv else conv["messages"][-limit:]

    def add_message(self, cid, msg):
        conv = self._store.get(cid)
        if conv:
            conv["messages"].append(msg)


class EvidenceBuilder:
    def build_evidence(self, exec_result):
        rc = exec_result.get("row_count", 0)
        if rc > 0:
            col = (exec_result.get("columns") or ["unknown"])[0]
            return [EvidenceReferenceDTO(evidence_id=str(uuid.uuid4()), evidence_type="database_fact",
                                         source_table=col, source_record_count=rc,
                                         display_label=f"{rc} records retrieved")]
        return []


CRIME_KEYWORDS = {
    "theft": "Theft", "murder": "Murder", "robbery": "Robbery",
    "assault": "Assault", "burglary": "Burglary", "kidnapping": "Kidnapping",
    "cheating": "Cheating", "snatching": "Snatching",
    "cyber": "Cyber Crime",
}

# Map colloquial place names → exact DistrictName in DB
# Special key "__all__" means skip the filter (state-level or unknown region)
# ponytail: static map, covers common Karnataka queries; expand if users ask for smaller taluks
PLACE_DISTRICT_MAP = {
    "karnataka": "__all__",
    "bangalore": "Bangalore Urban",
    "bengaluru": "Bangalore Urban",
    "bangalore urban": "Bangalore Urban",
    "bangalore rural": "Bangalore Rural",
    "mysuru": "Mysuru",
    "mysore": "Mysuru",
    "hubli": "Hubli",
    "mangalore": "Mangalore",
    "mangaluru": "Mangalore",
    "belgaum": "Belgaum",
    "belagavi": "Belgaum",
    "dharwad": "Dharwad",
    "shivamogga": "Shivamogga",
    "shimoga": "Shivamogga",
    "tumkur": "Tumkur",
    "kalaburagi": "Kalaburagi",
    "gulbarga": "Kalaburagi",
}

# Map status keywords → CaseStatusName in DB
STATUS_MAP = {
    "under investigation": "Under Investigation",
    "active": "Under Investigation",
    "charge sheet filed": "Charge Sheet Filed",
    "charge sheet": "Charge Sheet Filed",
    "court proceedings": "Court Proceedings",
    "court": "Court Proceedings",
    "closed": "Closed",
}

TOTAL_RE = re.compile(r"(total|count|how many)\s+(cases|firs)", re.I)
STATS_RE = re.compile(r"(crime\s+)?statistics|summary|overview", re.I)
ALL_CASES_RE = re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(cases|firs)", re.I)
SHOW_CRIME_RE = re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(theft|murder|robbery|assault|burglary|kidnapping|cheating|snatching|cyber)\w*", re.I)
CASES_IN_RE = re.compile(r"(cases|firs)(\s+in|\s+at|\s+for)?\s+(.+)$", re.I)
SPLIT_RE = re.compile(r"split|breakdown|per\s+(place|district|city|area)|by\s+(place|district|city|area)|each\s+(place|district)", re.I)
MAP_RE = re.compile(r"(show|on)\s+(a\s+)?map|map\s+view|where\s+are", re.I)
FOLLOWUP_DENY_RE = re.compile(r"^(show on map|compare with last year|which had arrests|show top 5 districts|show by district|by officer|overdue|pending)\s*$", re.I)
LOCATION_RE = re.compile(r'(?:in|at|for)\s+(\w+(?:\s+\w+)?)(?:\s+(?:district|city|area|region))?\s*$', re.I)
TEMPORAL_THIS_YEAR_RE = re.compile(r'\bthis\s+year\b', re.I)
TEMPORAL_LAST_YEAR_RE = re.compile(r'\blast\s+year\b', re.I)
TEMPORAL_YEAR_RE = re.compile(r'\b(202[0-9])\s+cases\b', re.I)
TEMPORAL_SINCE_RE = re.compile(r'\b(?:since|after|from)\s+(202[0-9])\b', re.I)


class ChatHandler:
    def __init__(self, catalyst_app=None):
        self.conversation_manager = InMemoryConversation()
        self.executor = QueryExecutor(catalyst_app)
        self.answer_gen = AnswerGenerator()
        self.evidence_builder = EvidenceBuilder()

    def _extract_place(self, msg: str) -> str:
        m = LOCATION_RE.search(msg)
        if m:
            return m.group(1).strip().lower()
        return ''

    def _location_clause(self, msg: str) -> str:
        place = self._extract_place(msg)
        if not place:
            return ''
        district_name = PLACE_DISTRICT_MAP.get(place)
        if not district_name:
            return ''
        if district_name == "__all__":
            return ''
        dist_result = self.executor.execute(
            f"SELECT DistrictID FROM District WHERE DistrictName = '{district_name}'"
        )
        if dist_result.get("error") or dist_result.get("row_count", 0) == 0:
            return ''
        dist_id = dist_result["rows"][0][0]
        unit_result = self.executor.execute(
            f"SELECT UnitID FROM Unit WHERE DistrictID = {dist_id}"
        )
        if unit_result.get("error") or unit_result.get("row_count", 0) == 0:
            return ''
        unit_ids = [str(r[0]) for r in unit_result.get("rows", []) if r]
        if not unit_ids:
            return ''
        return f"PoliceStationID IN ({','.join(unit_ids)})"

    def _status_clause(self, msg: str) -> str:
        for key, status_name in STATUS_MAP.items():
            if key in msg:
                result = self.executor.execute(
                    f"SELECT CaseStatusID FROM CaseStatusMaster WHERE CaseStatusName = '{status_name}'"
                )
                if not result.get("error") and result.get("row_count", 0) > 0:
                    sid = result["rows"][0][0]
                    return f"CaseStatusID = {sid}"
        return ''

    def _temporal_clause(self, msg: str) -> str:
        now = datetime.now()
        if TEMPORAL_THIS_YEAR_RE.search(msg):
            return f"CrimeRegisteredDate >= '{now.year}-01-01'"
        if TEMPORAL_LAST_YEAR_RE.search(msg):
            return (f"CrimeRegisteredDate >= '{now.year - 1}-01-01' "
                    f"AND CrimeRegisteredDate < '{now.year}-01-01'")
        m = TEMPORAL_YEAR_RE.search(msg)
        if m:
            y = m.group(1)
            return f"CrimeRegisteredDate >= '{y}-01-01' AND CrimeRegisteredDate < '{int(y) + 1}-01-01'"
        m = TEMPORAL_SINCE_RE.search(msg)
        if m:
            return f"CrimeRegisteredDate >= '{m.group(1)}-01-01'"
        return ''

    def _build_where(self, *clauses: str) -> str:
        non_empty = [c for c in clauses if c]
        return ' WHERE ' + ' AND '.join(non_empty) if non_empty else ''

    def _case_cols(self, extra: str = '') -> str:
        cols = 'ROWID, CaseNo, CrimeNo, CrimeRegisteredDate'
        return f'{cols}, {extra}' if extra else cols

    def _match_common_query(self, message: str) -> str:
        msg = message.strip().lower()
        if FOLLOWUP_DENY_RE.search(msg):
            return "SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, latitide, longitude, BriedFacts FROM CaseMaster LIMIT 50"
        if TOTAL_RE.search(msg):
            return "SELECT COUNT(ROWID) AS total_cases FROM CaseMaster"
        if STATS_RE.search(msg) or SPLIT_RE.search(msg):
            return "SELECT CrimeMinorHeadID, COUNT(ROWID) AS cnt FROM CaseMaster GROUP BY CrimeMinorHeadID"
        if MAP_RE.search(msg):
            return "SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, latitide, longitude, BriedFacts FROM CaseMaster WHERE latitide IS NOT NULL LIMIT 50"

        # Extract filter clauses — they work independently
        loc_clause = self._location_clause(msg)
        status_clause = self._status_clause(msg)
        temporal_clause = self._temporal_clause(msg)
        where = self._build_where(loc_clause, status_clause, temporal_clause)

        # Crime-type specific — runs its own lookup, appends extra filters
        m = SHOW_CRIME_RE.search(msg)
        if m:
            keyword = m.group(3).lower().rstrip('s')
            canonical = CRIME_KEYWORDS.get(keyword)
            if canonical:
                lookup = self.executor.execute(
                    f"SELECT CrimeSubHeadID FROM CrimeSubHead WHERE CrimeHeadName = '{canonical}'"
                )
                if not lookup.get("error") and lookup.get("row_count", 0) > 0:
                    ids = [str(r[0]) for r in lookup.get("rows", []) if r]
                    if ids:
                        crime_where = f"CrimeMinorHeadID IN ({','.join(ids)})"
                        extra = f"CrimeMinorHeadID, BriedFacts"
                        w = self._build_where(crime_where, loc_clause, status_clause, temporal_clause)
                        return f"SELECT {self._case_cols(extra)} FROM CaseMaster{w} LIMIT 50"
                w = self._build_where(loc_clause, status_clause, temporal_clause)
                return f"SELECT {self._case_cols('BriedFacts')} FROM CaseMaster{w} LIMIT 50"

        # Only location/status/temporal filters
        if loc_clause or status_clause or temporal_clause:
            return f"SELECT {self._case_cols('BriedFacts')} FROM CaseMaster{where} LIMIT 50"

        # Show all / catch-all
        return "SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, BriedFacts FROM CaseMaster LIMIT 50"

    def handle_query(self, req: QueryRequestDTO, user_context=None) -> ConversationMessageDTO:
        conv_id = req.conversation_id
        if not conv_id:
            conv_id = self.conversation_manager.create_conversation(
                user_context.user_id if user_context else "anonymous",
                language_code=req.lang
            )

        context = self.conversation_manager.get_context(conv_id)
        msg_lower = req.message.strip().lower().rstrip('?.!')
        greetings = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "namaste"}
        identity_queries = {"what is your name", "who are you", "what are you", "tell me about yourself", "your name", "who made you"}

        if msg_lower in greetings or any(g in msg_lower for g in {"hello ", "hi ", "hey "}):
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text="Hello! I am Suraksha AI, your crime intelligence assistant for Karnataka. How can I help you today?",
                content_kannada="ನಮಸ್ಕಾರ! ನಾನು ಸುರಕ್ಷಾ AI, ಕರ್ನಾಟಕದ ಅಪರಾಧ ಗುಪ್ತಚರ ಸಹಾಯಕ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
                confidence_class="high", grounding_status="verified",
                suggested_followups=["Show theft cases", "Show hotspot areas", "Predict future trends"],
                created_at=datetime.now().isoformat()
            )

        if any(q in msg_lower for q in identity_queries):
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text="I am Suraksha AI, an AI-powered Crime Intelligence and Analytics platform built for the Karnataka State Police to assist in crime tracking, forecasting, and offender profiling.",
                content_kannada="ನಾನು ಸುರಕ್ಷಾ AI, ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್‌ಗಾಗಿ ಅಪರಾಧ ಪತ್ತೆ ಹಚ್ಚುವಿಕೆ, ಮುನ್ಸೂಚನೆ ಮತ್ತು ಅಪರಾಧಿಗಳ ಪ್ರೊಫೈಲಿಂಗ್‌ನಲ್ಲಿ ಸಹಾಯ ಮಾಡಲು ನಿರ್ಮಿಸಲಾದ AI-ಆಧಾರಿತ ಅಪರಾಧ ಗುಪ್ತಚರ ಮತ್ತು ವಿಶ್ಲೇಷಣಾ ವೇದಿಕೆ.",
                confidence_class="high", grounding_status="verified",
                suggested_followups=["Show theft cases", "Show hotspot areas", "Predict future trends"],
                created_at=datetime.now().isoformat()
            )

        sql_text = self._match_common_query(req.message)

        exec_result = self.executor.execute(sql_text)
        if exec_result.get("error"):
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text=f"{exec_result.get('message', 'Query execution failed')} | Generated SQL: {sql_text}",
                confidence_class="low", grounding_status="unverified",
                created_at=datetime.now().isoformat()
            )

        evidence = self.evidence_builder.build_evidence(exec_result)
        answer = self.answer_gen.generate(exec_result, req.message)

        msg = ConversationMessageDTO(
            message_id=str(uuid.uuid4()), conversation_id=conv_id,
            message_type="ai_response", content_text=answer,
            sql_text=sql_text,
            query_id=exec_result.get("query_id"),
            evidence_refs=evidence,
            confidence_class="high", grounding_status="verified",
            suggested_followups=self._generate_followups(exec_result),
            created_at=datetime.now().isoformat()
        )
        self.conversation_manager.add_message(conv_id, msg)
        return msg

    def _generate_followups(self, exec_result):
        f = ["Show on map", "Compare with last year", "Which had arrests?"]
        if exec_result.get("row_count", 0) > 0:
            f.append("Show top 5 districts")
        return f
