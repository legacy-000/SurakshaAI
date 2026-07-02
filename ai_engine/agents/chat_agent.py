from typing import Any, Dict
from ai_engine.quickml_adapter import QuickMLAdapter

class ChatAgent:
    """
    AI Agent that processes user query, coordinates with QuickML RAG and returns response.
    Uses Zoho Catalyst QuickML instead of direct LangChain/OpenAI integration.
    """
    def __init__(self):
        self.quickml = QuickMLAdapter()

    def process_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        # Use QuickML RAG to get context-aware response
        rag_response = self.quickml.rag_query(message, "crime_documents")
        
        response_text = rag_response.get("answer", "I couldn't find an answer to your query.")
        
        return {
            "response": response_text,
            "session_id": session_id,
            "agent_metadata": {
                "engine": "Catalyst QuickML RAG",
                "source_documents": rag_response.get("source_documents", [])
            }
        }
