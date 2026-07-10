from models.dto import ConversationMessageDTO, QueryExecutionResultDTO


class GroundingValidator:
    def validate(self, message: ConversationMessageDTO, execution: QueryExecutionResultDTO) -> dict:
        if not execution or execution.execution_status != "success":
            return {"status": "unverified", "reason": "No successful execution to verify against"}

        if execution.row_count == 0 and "no" not in message.content_text.lower():
            return {"status": "partial", "reason": "Response mentions data but execution returned empty"}

        return {"status": "verified", "reason": "Response grounded in query results"}
