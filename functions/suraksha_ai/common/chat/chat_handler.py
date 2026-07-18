import json
import uuid
import re
from datetime import datetime

from models.dto import (
    QueryRequestDTO, ConversationMessageDTO, EvidenceReferenceDTO
)
from common.sql.query_executor import QueryExecutor
from common.ai.answer_generator import AnswerGenerator
from common.ai.quickml_client import QuickMLClient
from common.ai.tool_executor import ToolExecutor
from common.ai.query_policy import QueryPolicy
from common.ai.schema_registry import data_quality_warnings
from common.ai.confidence_classifier import ConfidenceClassifier
from common.ai.grounding_validator import GroundingValidator


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
            return [EvidenceReferenceDTO(
                evidence_id=str(uuid.uuid4()), evidence_type="database_fact",
                source_table=exec_result.get("tool_params", {}).get("table"),
                source_record_count=rc,
                display_label=f"{rc} records from {exec_result.get('tool_params', {}).get('table', 'database')}"
            )]
        return []


CRIME_KEYWORDS = {
    "theft": "Theft", "murder": "Murder", "robbery": "Robbery",
    "assault": "Assault", "burglary": "Burglary", "kidnapping": "Kidnapping",
    "cheating": "Cheating", "snatching": "Snatching",
    "cyber": "Cyber Crime",
}

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
SHOW_CRIME_RE = re.compile(
    r"(show|list|find|get)\s+(me\s+|all\s+)?(theft|murder|robbery|assault|burglary|kidnapping|cheating|snatching|cyber)\w*",
    re.I)
CASES_IN_RE = re.compile(r"(cases|firs)(\s+in|\s+at|\s+for)?\s+(.+)$", re.I)
SPLIT_RE = re.compile(
    r"split|breakdown|per\s+(place|district|city|area)|by\s+(place|district|city|area)|each\s+(place|district)",
    re.I)
MAP_RE = re.compile(r"(show|on)\s+(a\s+)?map|map\s+view|where\s+are", re.I)
FOLLOWUP_DENY_RE = re.compile(
    r"^(show on map|compare with last year|which had arrests|show top 5 districts|show by district|by officer|overdue|pending)\s*$",
    re.I)
LOCATION_RE = re.compile(r'(?:in|at|for)\s+(\w+(?:\s+\w+)?)(?:\s+(?:district|city|area|region))?\s*$', re.I)
TEMPORAL_THIS_YEAR_RE = re.compile(r'\bthis\s+year\b', re.I)
TEMPORAL_LAST_YEAR_RE = re.compile(r'\blast\s+year\b', re.I)
TEMPORAL_YEAR_RE = re.compile(r'\b(202[0-9])\s+cases\b', re.I)
TEMPORAL_SINCE_RE = re.compile(r'\b(?:since|after|from)\s+(202[0-9])\b', re.I)

# ponytail: regex patterns for all 26 tables — covers common NL queries across the full schema
LOOKUP_PATTERNS = [
    # Accused
    (re.compile(r"(total|count|how many)\s+(accused)", re.I),
     "SELECT COUNT(ROWID) AS total_accused FROM Accused"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(accused|offenders)", re.I),
     "SELECT ROWID, AccusedName, AgeYear, GenderID, PersonID FROM Accused LIMIT 50"),
    (re.compile(r"(accused|offender)\s+(details|profile|info)", re.I),
     "SELECT ROWID, AccusedName, AgeYear, GenderID, PersonID FROM Accused LIMIT 50"),
    # Victim
    (re.compile(r"(total|count|how many)\s+(victims)", re.I),
     "SELECT COUNT(ROWID) AS total_victims FROM Victim"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(victims)", re.I),
     "SELECT ROWID, VictimName, AgeYear, GenderID FROM Victim LIMIT 50"),
    # Complainant
    (re.compile(r"(total|count|how many)\s+(complainants)", re.I),
     "SELECT COUNT(ROWID) AS total_complainants FROM ComplainantDetails"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(complainants)", re.I),
     "SELECT ROWID, ComplainantName, AgeYear FROM ComplainantDetails LIMIT 50"),
    # Act / Section
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(acts|ipc|legal\s+acts)", re.I),
     "SELECT ActCode, ShortName, ActDescription FROM Act WHERE Active = true"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(sections|legal\s+sections)", re.I),
     "SELECT ActCode, SectionCode, SectionDescription FROM Section WHERE Active = true LIMIT 50"),
    # Chargesheet
    (re.compile(r"(total|count|how many)\s+(chargesheets|charge\s+sheets)", re.I),
     "SELECT COUNT(ROWID) AS total_chargesheets FROM ChargesheetDetails"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(chargesheets|charge\s+sheets)", re.I),
     "SELECT CSID, CaseMasterID, csdate, cstype FROM ChargesheetDetails LIMIT 50"),
    # Arrest
    (re.compile(r"(total|count|how many)\s+(arrests|arrest\s+records)", re.I),
     "SELECT COUNT(ROWID) AS total_arrests FROM ArrestSurrender"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(arrests|arrest\s+records)", re.I),
     "SELECT ROWID, CaseMasterID, ArrestSurrenderDate, PoliceStationID FROM ArrestSurrender LIMIT 50"),
    # Employee / Officer
    (re.compile(r"(total|count|how many)\s+(officers|employees|personnel)", re.I),
     "SELECT COUNT(ROWID) AS total_officers FROM Employee"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(officers|employees|police\s+personnel)", re.I),
     "SELECT EmployeeID, FirstName, UnitID FROM Employee LIMIT 50"),
    # District
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(districts)", re.I),
     "SELECT DistrictID, DistrictName FROM District WHERE Active = true"),
    # Unit / Police Station
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(police\s+stations|units)", re.I),
     "SELECT UnitID, UnitName, DistrictID FROM Unit WHERE Active = true LIMIT 50"),
    # Crime Type
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(crime\s+types|crime\s+categories|offence\s+types)", re.I),
     "SELECT CrimeSubHeadID, CrimeHeadID, CrimeHeadName FROM CrimeSubHead"),
    # Court
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(courts)", re.I),
     "SELECT CourtID, CourtName, DistrictID FROM Court WHERE Active = true"),
    # Case Status
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(case\s+status|status\s+list)", re.I),
     "SELECT CaseStatusID, CaseStatusName FROM CaseStatusMaster"),
    # Occupation / Caste / Religion lookups
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(occupations)", re.I),
     "SELECT OccupationID, OccupationName FROM OccupationMaster"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(castes|caste\s+list)", re.I),
     "SELECT caste_master_id, caste_master_name FROM CasteMaster"),
    (re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(religions|religion\s+list)", re.I),
     "SELECT ReligionID, ReligionName FROM ReligionMaster"),
]


class ChatHandler:
    def __init__(self, catalyst_app=None):
        self.conversation_manager = InMemoryConversation()
        self.executor = QueryExecutor(catalyst_app)
        self.answer_gen = AnswerGenerator()
        self.evidence_builder = EvidenceBuilder()
        self._glm = QuickMLClient(catalyst_app)
        self._tool_executor = ToolExecutor(catalyst_app)
        self._policy = QueryPolicy()
        self._system_prompt = self._tool_executor.system_prompt
        self._tool_def = self._tool_executor.tool_def
        self._confidence = ConfidenceClassifier()
        self._grounding = GroundingValidator()

    # ── Row-scope injection ──────────────────────────────────────────────
    def _user_scope(self, user_context) -> str:
        """Return a WHERE clause restricting to the user's unit/district, or ''."""
        if not user_context:
            return ''
        unit_id = getattr(user_context, 'unit_id', None)
        district_id = getattr(user_context, 'district_id', None)
        if unit_id:
            return f"PoliceStationID = {unit_id}"
        if district_id:
            units = self.executor.execute(
                f"SELECT UnitID FROM Unit WHERE DistrictID = {district_id}"
            )
            if not units.get("error") and units.get("row_count", 0) > 0:
                ids = [str(r[0]) for r in units.get("rows", []) if r]
                if ids:
                    return f"PoliceStationID IN ({','.join(ids)})"
        return ''

    # ── Legacy regex helpers ─────────────────────────────────────────────
    def _extract_place(self, msg: str) -> str:
        m = LOCATION_RE.search(msg)
        return m.group(1).strip().lower() if m else ''

    def _location_clause(self, msg: str) -> str:
        place = self._extract_place(msg)
        if not place:
            return ''
        district_name = PLACE_DISTRICT_MAP.get(place)
        if not district_name or district_name == "__all__":
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
        ids = [str(r[0]) for r in unit_result.get("rows", []) if r]
        return f"PoliceStationID IN ({','.join(ids)})" if ids else ''

    def _status_clause(self, msg: str) -> str:
        for key, status_name in STATUS_MAP.items():
            if key in msg:
                result = self.executor.execute(
                    f"SELECT CaseStatusID FROM CaseStatusMaster WHERE CaseStatusName = '{status_name}'"
                )
                if not result.get("error") and result.get("row_count", 0) > 0:
                    return f"CaseStatusID = {result['rows'][0][0]}"
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

    def _match_common_query(self, message: str) -> tuple:
        """Return (sql: str, warnings: list). Matches regex patterns; falls back to CaseMaster."""
        msg = message.strip().lower()
        warnings = []

        if FOLLOWUP_DENY_RE.search(msg):
            return ("SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, latitide, longitude, BriedFacts "
                    "FROM CaseMaster LIMIT 50"), warnings
        if TOTAL_RE.search(msg):
            return "SELECT COUNT(ROWID) AS total_cases FROM CaseMaster", warnings
        if STATS_RE.search(msg) or SPLIT_RE.search(msg):
            return ("SELECT CrimeMinorHeadID, COUNT(ROWID) AS cnt FROM CaseMaster "
                    "GROUP BY CrimeMinorHeadID"), warnings
        if MAP_RE.search(msg):
            return ("SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, latitide, longitude, BriedFacts "
                    "FROM CaseMaster WHERE latitide IS NOT NULL LIMIT 50"), warnings

        # Non-CaseMaster lookups
        for pattern, sql in LOOKUP_PATTERNS:
            if pattern.search(msg):
                return sql, warnings

        # Crime-type + filters
        loc_clause = self._location_clause(msg)
        status_clause = self._status_clause(msg)
        temporal_clause = self._temporal_clause(msg)

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
                        w = self._build_where(crime_where, loc_clause, status_clause, temporal_clause)
                        return f"SELECT {self._case_cols('CrimeMinorHeadID, BriedFacts')} FROM CaseMaster{w} LIMIT 50", warnings
            w = self._build_where(loc_clause, status_clause, temporal_clause)
            return f"SELECT {self._case_cols('BriedFacts')} FROM CaseMaster{w} LIMIT 50", warnings

        if loc_clause or status_clause or temporal_clause:
            w = self._build_where(loc_clause, status_clause, temporal_clause)
            return f"SELECT {self._case_cols('BriedFacts')} FROM CaseMaster{w} LIMIT 50", warnings

        return ("SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, BriedFacts FROM CaseMaster LIMIT 50"), warnings

    # ── GLM tool-calling ─────────────────────────────────────────────────
    def _try_glm_tool_call(self, message: str, user_context=None) -> dict:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": message},
        ]
        result = self._glm.chat(messages, temperature=0.1, max_tokens=2048,
                                tools=[self._tool_def], tool_choice="auto")
        if result.get("error"):
            return result

        if result.get("has_tool_call"):
            tool_calls = result.get("tool_calls", [])
            for tc in tool_calls:
                exec_result = self._tool_executor.execute_tool_call(tc)
                if exec_result.get("error"):
                    return exec_result

                # Enforce policy
                table = exec_result.get("tool_params", {}).get("table", "")
                policy_warnings = self._policy.enforce(exec_result.get("tool_params", {}))
                # Data-quality warnings
                cols = exec_result.get("tool_params", {}).get("columns", [])
                quality_warnings = data_quality_warnings(table, cols)
                all_warnings = policy_warnings + quality_warnings
                exec_result["warnings"] = all_warnings
                exec_result["quality_warnings"] = quality_warnings

                # Row-scope: inject user scope if the query is on CaseMaster
                scope = self._user_scope(user_context)
                if scope and table == "CaseMaster":
                    zcql = exec_result.get("generated_zcql", "")
                    if "WHERE" in zcql.upper():
                        zcql = zcql.replace("WHERE ", f"WHERE {scope} AND ", 1)
                    else:
                        idx = zcql.upper().rfind("LIMIT")
                        if idx > 0:
                            zcql = zcql[:idx] + f" WHERE {scope} " + zcql[idx:]
                        else:
                            zcql += f" WHERE {scope}"
                    exec_result["generated_zcql"] = zcql
                    re_run = self.executor.execute(zcql)
                    if not re_run.get("error"):
                        exec_result["rows"] = re_run.get("rows", [])
                        exec_result["row_count"] = re_run.get("row_count", 0)
                        exec_result["columns"] = re_run.get("columns", [])
                    exec_result["row_scope_applied"] = bool(scope)

                # Feed result back to GLM for composition
                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "content": json.dumps({
                        "row_count": exec_result.get("row_count", 0),
                        "columns": exec_result.get("columns", []),
                        "rows": exec_result.get("rows", []),
                    })
                }
                messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
                messages.append(tool_result_msg)

                compose = self._glm.chat(messages, temperature=0.1, max_tokens=1024)
                if compose.get("error"):
                    return compose

                return {
                    "text": compose.get("text", ""),
                    "sql_text": exec_result.get("generated_zcql", ""),
                    "tool_params": exec_result.get("tool_params", {}),
                    "row_count": exec_result.get("row_count", 0),
                    "columns": exec_result.get("columns", []),
                    "rows": exec_result.get("rows", []),
                    "warnings": all_warnings,
                    "quality_warnings": quality_warnings,
                    "source": "glm_tool_call",
                }

        return {"text": result.get("text", ""), "source": "glm_text"}

    # ── Main handler ─────────────────────────────────────────────────────
    def handle_query(self, req: QueryRequestDTO, user_context=None) -> ConversationMessageDTO:
        conv_id = req.conversation_id
        if not conv_id:
            conv_id = self.conversation_manager.create_conversation(
                user_context.user_id if user_context else "anonymous",
                language_code=req.lang
            )

        msg_lower = req.message.strip().lower().rstrip('?.!')
        greetings = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "namaste"}
        identity_queries = {
            "what is your name",
            "who are you",
            "what are you",
            "tell me about yourself",
            "your name",
            "who made you"}

        if msg_lower in greetings or any(g in msg_lower for g in {"hello ", "hi ", "hey "}):
            resp = self._try_glm_tool_call(req.message, user_context)
            content_text = resp.get("text") if not resp.get("error") else None
            return ConversationMessageDTO(
                message_id=str(
                    uuid.uuid4()),
                conversation_id=conv_id,
                message_type="ai_response",
                content_text=content_text or "Hello! I am Suraksha AI, your crime intelligence assistant for Karnataka. How can I help you today?",
                content_kannada="ನಮಸ್ಕಾರ! ನಾನು ಸುರಕ್ಷಾ AI, ಕರ್ನಾಟಕದ ಅಪರಾಧ ಗುಪ್ತಚರ ಸಹಾಯಕ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
                confidence_class="high",
                grounding_status="verified",
                suggested_followups=[
                    "Show theft cases",
                    "Show hotspot areas",
                    "Predict future trends"],
                created_at=datetime.now().isoformat())

        if any(q in msg_lower for q in identity_queries):
            resp = self._try_glm_tool_call(req.message, user_context)
            content_text = resp.get("text") if not resp.get("error") else None
            return ConversationMessageDTO(
                message_id=str(
                    uuid.uuid4()),
                conversation_id=conv_id,
                message_type="ai_response",
                content_text=content_text or "I am Suraksha AI, an AI-powered Crime Intelligence and Analytics platform built for the Karnataka State Police.",
                content_kannada="ನಾನು ಸುರಕ್ಷಾ AI, ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್‌ಗಾಗಿ ಅಪರಾಧ ಪತ್ತೆ ಹಚ್ಚುವಿಕೆ, ಮುನ್ಸೂಚನೆ ಮತ್ತು ಅಪರಾಧಿಗಳ ಪ್ರೊಫೈಲಿಂಗ್‌ನಲ್ಲಿ ಸಹಾಯ ಮಾಡಲು ನಿರ್ಮಿಸಲಾದ AI-ಆಧಾರಿತ ಅಪರಾಧ ಗುಪ್ತಚರ ಮತ್ತು ವಿಶ್ಲೇಷಣಾ ವೇದಿಕೆ.",
                confidence_class="high",
                grounding_status="verified",
                suggested_followups=[
                    "Show theft cases",
                    "Show hotspot areas",
                    "Predict future trends"],
                created_at=datetime.now().isoformat())

        # Try GLM tool-calling first
        glm_result = self._try_glm_tool_call(req.message, user_context)
        if not glm_result.get("error") and glm_result.get("text"):
            source = glm_result.get("source", "")
            if source == "glm_tool_call":
                sql_text = glm_result.get("sql_text", "")
                exec_res = {
                    "row_count": glm_result.get("row_count", 0),
                    "columns": glm_result.get("columns", []),
                    "rows": glm_result.get("rows", []),
                    "source": "glm_tool_call",
                    "quality_warnings": glm_result.get("quality_warnings", []),
                }
                evidence = self.evidence_builder.build_evidence(exec_res)
                answer = glm_result.get("text", "")
                warnings = glm_result.get("warnings", [])
                quality_warnings = glm_result.get("quality_warnings", [])
                tool_params = glm_result.get("tool_params", {})
            else:
                sql_text = ""
                evidence = []
                exec_res = {"row_count": 0, "source": "glm_text"}
                answer = glm_result.get("text", "")
                warnings = []
                quality_warnings = []
                tool_params = {}

            cc = self._confidence.classify(exec_res)
            gv = self._grounding.validate(answer, exec_res)
            msg = ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response", content_text=answer,
                content_kannada=self._translate_answer(answer),
                sql_text=sql_text, evidence_refs=evidence,
                confidence_class=cc, grounding_status=gv,
                suggested_followups=self._generate_followups(exec_res),
                data_quality_warnings=warnings + quality_warnings,
                tool_params=tool_params,
                created_at=datetime.now().isoformat()
            )
            self.conversation_manager.add_message(conv_id, msg)
            return msg

        # Fallback: regex
        sql_text, _warnings = self._match_common_query(req.message)
        exec_result = self.executor.execute(sql_text)
        if exec_result.get("error"):
            err_msg = f"{exec_result.get('message', 'Query execution failed')} | Generated SQL: {sql_text}"
            err_msg_kn = f"{self._translate_answer(exec_result.get('message', 'Query execution failed'))} | Generated SQL: {sql_text}"
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text=err_msg,
                content_kannada=err_msg_kn,
                confidence_class=self._confidence.classify(exec_result),
                grounding_status=self._grounding.validate("", exec_result),
                created_at=datetime.now().isoformat()
            )

        answer = self.answer_gen.generate(exec_result, req.message)
        evidence = self.evidence_builder.build_evidence(exec_result)
        cc = self._confidence.classify(exec_result)
        gv = self._grounding.validate(answer, exec_result)
        msg = ConversationMessageDTO(
            message_id=str(uuid.uuid4()), conversation_id=conv_id,
            message_type="ai_response", content_text=answer,
            content_kannada=self._translate_answer(answer),
            sql_text=sql_text, query_id=exec_result.get("query_id"),
            evidence_refs=evidence,
            confidence_class=cc, grounding_status=gv,
            suggested_followups=self._generate_followups(exec_result),
            created_at=datetime.now().isoformat()
        )
        self.conversation_manager.add_message(conv_id, msg)
        return msg

    def _translate_answer(self, answer: str) -> str:
        from common.i18n.translation_manager import TranslationManager
        translated = TranslationManager().translate(answer, 'kn')
        if translated != answer:
            return translated

        import re
        places_kn = {
            "bangalore": "ಬೆಂಗಳೂರು",
            "bengaluru": "ಬೆಂಗಳೂರು",
            "mysuru": "ಮೈಸೂರು",
            "mysore": "ಮೈಸೂರು",
            "mangalore": "ಮಂಗಳೂರು",
            "mangaluru": "ಮಂಗಳೂರು",
            "hubli": "ಹುಬ್ಬಳ್ಳಿ",
            "belgaum": "ಬೆಳಗಾವಿ",
            "belagavi": "ಬೆಳಗಾವಿ",
            "dharwad": "ಧಾರವಾಡ",
            "shivamogga": "ಶಿವಮೊಗ್ಗ",
            "tumkur": "ತುಮಕೂರು",
            "kalaburagi": "ಕಲಬುರಗಿ",
        }
        crimes_kn = {
            "theft": "ಕಳ್ಳತನ",
            "robbery": "ದರೋಡೆ",
            "assault": "ಹಲ್ಲೆ",
            "murder": "ಕೊಲೆ",
            "burglary": "ಕನ್ನಗಳವು",
            "kidnapping": "ಅಪಹರಣ",
            "cyber": "ಸೈಬರ್ ಅಪರಾಧ",
        }

        # 1. "I found (\d+) (\w+)\s*cases in (\w+(?:\s+\w+)?)\b"
        m = re.search(r"I found (\d+) (\w+)\s*cases in (\w+(?:\s+\w+)?)\b", answer, re.I)
        if m:
            count = m.group(1)
            crime = m.group(2).lower()
            place = m.group(3).lower()
            crime_kn = crimes_kn.get(crime, crime)
            place_kn = places_kn.get(place, place.capitalize())
            return f"{place_kn} ನಲ್ಲಿ {count} {crime_kn} ಪ್ರಕರಣಗಳು ಕಂಡುಬಂದಿವೆ."

        # 2. "I found (\d+) cases in (\w+(?:\s+\w+)?)\b"
        m = re.search(r"I found (\d+) cases in (\w+(?:\s+\w+)?)\b", answer, re.I)
        if m:
            count = m.group(1)
            place = m.group(2).lower()
            place_kn = places_kn.get(place, place.capitalize())
            return f"{place_kn} ನಲ್ಲಿ {count} ಪ್ರಕರಣಗಳು ಕಂಡುಬಂದಿವೆ."

        # 3. "Found (\d+) records\."
        m = re.search(r"Found (\d+) records\b", answer, re.I)
        if m:
            return f"{m.group(1)} ಪ್ರಕರಣಗಳು ಕಂಡುಬಂದಿವೆ."

        # 4. "No records found matching your query."
        if "no records found" in answer.lower():
            return "ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಯಾವುದೇ ಪ್ರಕರಣಗಳು ತಾಳೆಯಾಗುತ್ತಿಲ್ಲ."

        # Otherwise split and translate key crime/place words
        words = answer.split()
        translated_words = []
        for w in words:
            w_clean = w.lower().strip(".,?!")
            w_kn = places_kn.get(w_clean) or crimes_kn.get(w_clean)
            if w_kn:
                suffix = w[len(w_clean):]
                translated_words.append(w_kn + suffix)
            else:
                translated_words.append(w)
        return " ".join(translated_words)

    def _generate_followups(self, exec_result):
        f = ["Show on map", "Compare with last year", "Which had arrests?"]
        if exec_result.get("row_count", 0) > 0:
            f.append("Show top 5 districts")
        return f
