from typing import List, Dict, Any
from ai_engine.quickml_adapter import QuickMLAdapter

class RAGRetriever:
    """
    RAG Retriever using Catalyst QuickML Knowledge Base.
    """
    def __init__(self, knowledge_base_id: str = "crime_documents"):
        self.knowledge_base_id = knowledge_base_id
        self.quickml = QuickMLAdapter()

    def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves matching documents from QuickML Knowledge Base.
        """
        rag_response = self.quickml.rag_query(query, self.knowledge_base_id)
        
        # Transform QuickML response to standard document format
        documents = rag_response.get("source_documents", [])
        return documents[:top_k]
