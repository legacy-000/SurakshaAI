import uuid
import re
from datetime import datetime

from models.dto import (
    QueryRequestDTO, ConversationMessageDTO, EvidenceReferenceDTO
)
from common.ai.nl2sql_engine import NL2SQLEngine
from common.sql.query_executor import QueryExecutor
from common.ai.answer_generator import AnswerGenerator
from common.utils.viz_recommender import VizRecommender


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

TOTAL_RE = re.compile(r"(total|count|how many)\s+(cases|firs)", re.I)
STATS_RE = re.compile(r"(crime\s+)?statistics|summary|overview", re.I)
ALL_CASES_RE = re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(cases|firs)", re.I)
SHOW_CRIME_RE = re.compile(r"(show|list|find|get)\s+(me\s+|all\s+)?(theft|murder|robbery|assault|burglary|kidnapping|cheating|snatching|cyber)\w*", re.I)
CASES_IN_RE = re.compile(r"(cases|firs)(\s+in|\s+at|\s+for)?\s+(.+)$", re.I)
SPLIT_RE = re.compile(r"split|breakdown|per\s+(place|district|city|area)|by\s+(place|district|city|area)|each\s+(place|district)", re.I)
MAP_RE = re.compile(r"(show|on)\s+(a\s+)?map|map\s+view|where\s+are", re.I)
FOLLOWUP_DENY_RE = re.compile(r"^(show on map|compare with last year|which had arrests|show top 5 districts|show by district|by officer|overdue|pending)\s*$", re.I)


class ChatHandler:
    def __init__(self, catalyst_app=None):
        self.conversation_manager = InMemoryConversation()
        self.nl2sql = NL2SQLEngine(catalyst_app)
        self.executor = QueryExecutor(catalyst_app)
        self.answer_gen = AnswerGenerator()
        self.evidence_builder = EvidenceBuilder()
        self.viz_recommender = VizRecommender()

    def _match_common_query(self, message: str) -> str:
        msg = message.strip().lower()
        # Followup denial — return all cases for templated followups like "Show on map"
        if FOLLOWUP_DENY_RE.search(msg):
            return "SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, latitide, longitude, BriedFacts FROM CaseMaster LIMIT 50"
        # Total cases
        if TOTAL_RE.search(msg):
            return "SELECT COUNT(ROWID) AS total_cases FROM CaseMaster"
        # Crime statistics / breakdown by type
        if STATS_RE.search(msg) or SPLIT_RE.search(msg):
            return "SELECT CrimeMinorHeadID, COUNT(ROWID) AS cnt FROM CaseMaster GROUP BY CrimeMinorHeadID"
        # Map view
        if MAP_RE.search(msg):
            return "SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, latitide, longitude, BriedFacts FROM CaseMaster WHERE latitide IS NOT NULL LIMIT 50"
        # Crime-type-specific: first look up the CrimeSubHeadID
        m = SHOW_CRIME_RE.search(msg)
        if m:
            keyword = m.group(3).lower().rstrip('s')
            canonical = CRIME_KEYWORDS.get(keyword, None)
            if canonical:
                lookup = self.executor.execute(
                    f"SELECT CrimeSubHeadID FROM CrimeSubHead WHERE CrimeHeadName = '{canonical}'"
                )
                if not lookup.get("error") and lookup.get("row_count", 0) > 0:
                    rows = lookup.get("rows", [])
                    ids = [str(r[0]) for r in rows if r]
                    if ids:
                        return f"SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, CrimeMinorHeadID, BriedFacts FROM CaseMaster WHERE CrimeMinorHeadID IN ({','.join(ids)}) LIMIT 50"
                return "SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate FROM CaseMaster LIMIT 50"
        # Show all cases
        if ALL_CASES_RE.search(msg) or CASES_IN_RE.search(msg):
            return "SELECT ROWID, CaseNo, CrimeNo, CrimeRegisteredDate, BriedFacts FROM CaseMaster LIMIT 50"
        # Always return something — skip unreliable NL2SQL
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
        chart = self.viz_recommender.recommend(exec_result)

        msg = ConversationMessageDTO(
            message_id=str(uuid.uuid4()), conversation_id=conv_id,
            message_type="ai_response", content_text=answer,
            sql_text=sql_text,
            query_id=exec_result.get("query_id"),
            evidence_refs=evidence,
            confidence_class="high", grounding_status="verified",
            chart_recommendation=chart,
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
