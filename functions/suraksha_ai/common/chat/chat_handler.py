import uuid
from datetime import datetime

from common.models.dto import (
    QueryRequestDTO, ConversationMessageDTO, EvidenceReferenceDTO
)
from common.chat.conversation_manager import ConversationManager
from common.ai.nl2sql_engine import NL2SQLEngine
from common.sql.query_executor import QueryExecutor
from common.ai.answer_generator import AnswerGenerator
from common.evidence.evidence_builder import EvidenceBuilder
from common.utils.viz_recommender import VizRecommender
from common.auth.rbac_middleware import RBACMiddleware


class ChatHandler:
    def __init__(self, catalyst_app=None):
        self.conversation_manager = ConversationManager()
        self.nl2sql = NL2SQLEngine(catalyst_app)
        self.executor = QueryExecutor(catalyst_app)
        self.answer_gen = AnswerGenerator()
        self.evidence_builder = EvidenceBuilder()
        self.viz_recommender = VizRecommender()
        self.rbac = RBACMiddleware()

    def handle_query(self, req: QueryRequestDTO, user_context=None) -> ConversationMessageDTO:
        conv_id = req.conversation_id or str(uuid.uuid4())
        if not req.conversation_id:
            self.conversation_manager.create_conversation(
                user_context.user_id if user_context else "anonymous",
                language_code=req.lang
            )

        context = self.conversation_manager.get_context(conv_id)

        # Intercept greetings and identity queries
        msg_lower = req.message.strip().lower().rstrip('?.!')
        greetings = {"hi", "hello", "hey", "greetings", "good morning", "good afternoon", "good evening", "namaste"}
        identity_queries = {"what is your name", "who are you", "what are you", "tell me about yourself", "your name", "who made you"}

        if msg_lower in greetings or any(g in msg_lower for g in {"hello ", "hi ", "hey "}):
            answer = "Hello! I am Suraksha AI, your crime intelligence assistant for Karnataka. How can I help you today?"
            answer_kn = "ನಮಸ್ಕಾರ! ನಾನು ಸುರಕ್ಷಾ AI, ಕರ್ನಾಟಕದ ಅಪರಾಧ ಗುಪ್ತಚರ ಸಹಾಯಕ. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?"
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text=answer,
                content_kannada=answer_kn,
                confidence_class="high", grounding_status="verified",
                suggested_followups=["Show theft cases in Bangalore", "Show hotspot areas", "Predict future trends"],
                created_at=datetime.now().isoformat()
            )

        if any(q in msg_lower for q in identity_queries):
            answer = "I am Suraksha AI, an AI-powered Crime Intelligence and Analytics platform built for the Karnataka State Police to assist in crime tracking, forecasting, and offender profiling."
            answer_kn = "ನಾನು ಸುರಕ್ಷಾ AI, ಕರ್ನಾಟಕ ರಾಜ್ಯ ಪೊಲೀಸ್‌ಗಾಗಿ ಅಪರಾಧ ಪತ್ತೆ ಹಚ್ಚುವಿಕೆ, ಮುನ್ಸೂಚನೆ ಮತ್ತು ಅಪರಾಧಿಗಳ ಪ್ರೊಫೈಲಿಂಗ್‌ನಲ್ಲಿ ಸಹಾಯ ಮಾಡಲು ನಿರ್ಮಿಸಲಾದ AI-ಆಧಾರಿತ ಅಪರಾಧ ಗುಪ್ತಚರ ಮತ್ತು ವಿಶ್ಲೇಷಣಾ ವೇದಿಕೆ."
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text=answer,
                content_kannada=answer_kn,
                confidence_class="high", grounding_status="verified",
                suggested_followups=["Show theft cases in Bangalore", "Show hotspot areas", "Predict future trends"],
                created_at=datetime.now().isoformat()
            )

        sql_result = self.nl2sql.generate_sql(req.message, context=context)
        if sql_result.get("error"):
            err_msg = sql_result.get("message", "")
            if sql_result.get("error") == "SQLGEN_001":
                val = sql_result.get("validation", {})
                err_msg = f"SQL Validation failed. Reasons: {val.get('reasons', [])}. Generated SQL: {sql_result.get('sql_text')}"
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text=f"I could not generate a query for that request: {sql_result.get('error')} - {err_msg}",
                confidence_class="low", grounding_status="unverified",
                created_at=datetime.now().isoformat()
            )

        exec_result = self.executor.execute(sql_result["sql_text"])
        if exec_result.get("error"):
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text=f"{exec_result.get('message', 'Query execution failed')} | Generated SQL: {sql_result.get('sql_text')}",
                confidence_class="low", grounding_status="unverified",
                created_at=datetime.now().isoformat()
            )

        evidence = self.evidence_builder.build_evidence(exec_result)
        answer = self.answer_gen.generate(exec_result, req.message)
        chart = self.viz_recommender.recommend(exec_result)

        msg = ConversationMessageDTO(
            message_id=str(uuid.uuid4()), conversation_id=conv_id,
            message_type="ai_response", content_text=answer,
            sql_text=sql_result["sql_text"],
            query_id=exec_result.get("query_id"),
            evidence_refs=evidence,
            confidence_class="high", grounding_status="verified",
            chart_recommendation=chart,
            suggested_followups=self._generate_followups(exec_result),
            created_at=datetime.now().isoformat()
        )
        self.conversation_manager.add_message(conv_id, msg)
        return msg

    def _generate_followups(self, exec_result: dict) -> list[str]:
        followups = [
            "Show on map",
            "Compare with last year",
            "Which had arrests?"
        ]
        if exec_result.get("row_count", 0) > 0:
            followups.append("Show top 5 districts")
        return followups
