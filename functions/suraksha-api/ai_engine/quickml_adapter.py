import os
from typing import List, Dict, Any, Optional

try:
    from catalyst import Catalyst
    from catalyst.quickml import QuickML
    QUICKML_AVAILABLE = True
except ImportError:
    QUICKML_AVAILABLE = False


class QuickMLAdapter:
    """Adapter for Catalyst QuickML text generation and RAG."""

    def __init__(self, knowledge_base_id: str = "crime_documents"):
        self.knowledge_base_id = knowledge_base_id
        self.quickml = None
        if QUICKML_AVAILABLE:
            try:
                app = Catalyst.initialize()
                self.quickml = QuickML(app)
            except Exception:
                pass

    def generate_text(self, prompt: str, context: str = "", max_tokens: int = 500) -> str:
        if self.quickml:
            try:
                response = self.quickml.generate_text(prompt=prompt, context=context, max_tokens=max_tokens)
                return response.get("text", "")
            except Exception:
                pass
        return f"Simulated QuickML response for: {prompt[:50]}..."

    def rag_query(self, query: str, knowledge_base_id: str = None) -> Dict[str, Any]:
        if self.quickml:
            try:
                response = self.quickml.rag_query(query=query, knowledge_base_id=knowledge_base_id or self.knowledge_base_id)
                return response
            except Exception:
                pass
        return {"answer": f"Simulated answer for: {query}", "source_documents": []}

    def create_knowledge_base(self, name: str, documents: List[Dict[str, Any]]) -> str:
        if self.quickml:
            try:
                kb_id = self.quickml.create_knowledge_base(name, documents)
                return kb_id
            except Exception:
                pass
        return f"mock_kb_{name}"
