import uuid
from datetime import datetime

from models.dto import (
    QueryRequestDTO, ConversationMessageDTO, EvidenceReferenceDTO
)
from functions.chat.conversation_manager import ConversationManager
from functions.ai.nl2sql_engine import NL2SQLEngine
from functions.sql.query_executor import QueryExecutor
from functions.ai.answer_generator import AnswerGenerator
from functions.evidence.evidence_builder import EvidenceBuilder
from functions.utils.viz_recommender import VizRecommender
from functions.auth.rbac_middleware import RBACMiddleware


class ChatHandler:
    def __init__(self):
        self.conversation_manager = ConversationManager()
        self.nl2sql = NL2SQLEngine()
        self.executor = QueryExecutor()
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

        sql_result = self.nl2sql.generate_sql(req.message, context=context)
        if sql_result.get("error"):
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text="I could not generate a query for that request. Please try rephrasing.",
                confidence_class="low", grounding_status="unverified",
                created_at=datetime.now().isoformat()
            )

        exec_result = self.executor.execute(sql_result["sql_text"])
        if exec_result.get("error"):
            return ConversationMessageDTO(
                message_id=str(uuid.uuid4()), conversation_id=conv_id,
                message_type="ai_response",
                content_text=f"Query execution failed: {exec_result['error']}",
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
