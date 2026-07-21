from __future__ import annotations
import json
import logging
from common.ai.quickml_client import QuickMLClient
from common.ai.tool_executor import ToolExecutor

logger = logging.getLogger(__name__)

CRIME_KEYWORDS = {
    "theft": "Theft", "murder": "Murder", "robbery": "Robbery",
    "assault": "Assault", "burglary": "Burglary", "kidnapping": "Kidnapping",
    "cheating": "Cheating", "snatching": "Snatching",
    "cyber": "Cyber Crime",
}


class NetworkAIHandler:
    def __init__(self, catalyst_app=None, tool_executor=None):
        self._glm = QuickMLClient(catalyst_app)
        self._tool_executor = tool_executor or ToolExecutor(catalyst_app)
        self._system_prompt = self._build_system_prompt()
        self._tool_def = self._tool_executor.tool_def

    @property
    def is_available(self):
        return self._glm.is_available

    def _build_system_prompt(self) -> str:
        schema_prompt = self._tool_executor.system_prompt
        return (
            "You are NetworkAI, an AI investigation assistant for the Suraksha police platform. "
            "You help officers analyze criminal networks, relationships between accused, "
            "case linkages, risk assessment, and investigation leads.\n\n"
            "CAPABILITIES:\n"
            "1. Analyze the loaded network graph (nodes=accused/cases, edges=connections)\n"
            "2. Query the database using the query_datastore tool for case details, "
            "accused/victim/complainant info, crime statistics, and more\n"
            "3. Answer general questions and have natural conversation\n"
            "4. Reference earlier parts of the conversation\n\n"
            "GUIDELINES:\n"
            "- Be conversational, clear, and concise\n"
            "- Use the query_datastore tool when you need data not visible in the graph\n"
            "- When a network graph is loaded, use it to answer specifically\n"
            "- When no graph is loaded, guide the user to search\n"
            "- Respond in the language the user wrote in\n\n"
            f"{schema_prompt}"
        )

    def answer(self, question: str, history: list, nodes: list, edges: list) -> dict:
        if not question.strip():
            return {"answer": "Ask me anything about the network or cases!"}

        graph_context = self._summarize_graph(nodes, edges)

        # ponytail: greetings/help handled deterministically, no LLM call needed
        q = question.lower().strip().rstrip(".!?")
        greetings = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon", "howdy", "namaste"}
        if q in greetings:
            if nodes:
                return {"answer": f"Hello! I see a network with {len(nodes)} nodes loaded. Ask me about connections, risk, or cases.", "summary": graph_context}
            return {"answer": "Hello! I'm NetworkAI. Search for a person or case to load a network, and I'll help analyze it.", "summary": graph_context}
        if q in ("how are you", "how r u"):
            return {"answer": "I'm ready to help with your investigation. What would you like to explore?", "summary": graph_context}
        if q in ("what can you do", "help", "what do you do"):
            return {"answer": "I can analyze criminal networks, query case data, find co-accused links, assess risk, and answer questions about your data. Try loading a network graph or asking about a specific case or person.", "summary": graph_context}

        messages = [{"role": "system", "content": self._system_prompt}]
        for h in history[-10:]:
            role = "user" if h.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": h.get("text", "")})

        user_content = question
        if graph_context:
            user_content = f"[Loaded Network Graph]\n{graph_context}\n\n{question}"
        messages.append({"role": "user", "content": user_content})

        text = self._try_tool_call_loop(messages)
        if text:
            return {"answer": text, "summary": graph_context}

        text = self._try_direct_llm(messages)
        if text:
            return {"answer": text, "summary": graph_context}

        return {"answer": self._fallback(question, nodes, edges), "summary": graph_context}

    def _summarize_graph(self, nodes: list, edges: list) -> str:
        if not nodes and not edges:
            return ""
        accused = [n for n in nodes if n.get("node_type") == "accused"]
        cases = [n for n in nodes if n.get("node_type") == "case"]
        high = [n for n in accused if n.get("risk_tier") in ("HIGH", "ELEVATED")]
        degree = {}
        for e in edges:
            degree[e.get("source")] = degree.get(e.get("source"), 0) + 1
            degree[e.get("target")] = degree.get(e.get("target"), 0) + 1
        top3 = sorted(degree, key=degree.get, reverse=True)[:3]
        labels = []
        for nid in top3:
            for n in nodes:
                if n.get("id") == nid:
                    labels.append(n.get("label", nid))
                    break
        parts = [f"Nodes: {len(nodes)} ({len(accused)} accused, {len(cases)} cases), Edges: {len(edges)}."]
        if high:
            parts.append(f"High-risk: {', '.join(n['label'] for n in high[:5])}.")
        if labels:
            parts.append(f"Most connected: {', '.join(labels)}.")
        return " ".join(parts)

    def _try_tool_call_loop(self, messages: list) -> str | None:
        try:
            result = self._glm.chat(messages, temperature=0.3, max_tokens=1024,
                                    tools=[self._tool_def], tool_choice="auto")
            if result.get("error"):
                return None

            if not result.get("has_tool_call"):
                return result.get("text", "")

            tool_calls = result.get("tool_calls", [])
            for tc in tool_calls:
                exec_result = self._tool_executor.execute_tool_call(tc)
                if exec_result.get("error"):
                    return None

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

                compose = self._glm.chat(messages, temperature=0.3, max_tokens=512)
                if compose.get("error"):
                    return None
                return compose.get("text", "")
        except Exception as e:
            logger.warning("network_ai tool-call loop failed: %s", e)
        return None

    def _try_direct_llm(self, messages: list) -> str | None:
        try:
            result = self._glm.chat(messages, temperature=0.5, max_tokens=512)
            if result.get("error"):
                return None
            return result.get("text", "")
        except Exception:
            return None

    def _fallback(self, question: str, nodes: list, edges: list) -> str:
        q = question.lower().strip().rstrip(".!?")
        greetings = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon", "howdy", "namaste"}
        if q in greetings:
            if nodes:
                return f"Hello! I see a network with {len(nodes)} nodes loaded. Ask me about connections, risk, or cases."
            return "Hello! I'm NetworkAI. Search for a person or case to load a network, and I'll help analyze it."
        if q in ("how are you", "how r u"):
            return "I'm ready to help with your investigation. What would you like to explore?"
        if q in ("what can you do", "help", "what do you do"):
            return "I can analyze criminal networks, query case data, find co-accused links, assess risk, and answer questions about your data. Try loading a network graph or asking about a specific case or person."
        if not nodes:
            return "No network loaded. Search for a person or case number to get started."

        accused = [n for n in nodes if n.get("node_type") == "accused"]
        cases = [n for n in nodes if n.get("node_type") == "case"]
        high = [n for n in accused if n.get("risk_tier") in ("HIGH", "ELEVATED")]
        degree = {}
        for e in edges:
            degree[e.get("source")] = degree.get(e.get("source"), 0) + 1
            degree[e.get("target")] = degree.get(e.get("target"), 0) + 1
        top = sorted(degree, key=degree.get, reverse=True)[:3]
        labels = []
        for nid in top:
            for n in nodes:
                if n.get("id") == nid:
                    labels.append(n.get("label", nid))
                    break

        if "highest priority" in q or "most dangerous" in q or "risk" in q:
            if high:
                return "Highest priority: " + "; ".join(f"{n['label']} ({n.get('risk_tier','')}, {n.get('cases',0)} cases)" for n in high[:5])
            return "No high-risk individuals in this network."
        if "connection" in q or "link" in q:
            links = []
            for e in edges:
                src = next((n.get("label","") for n in nodes if n.get("id") == e.get("source")), "")
                tgt = next((n.get("label","") for n in nodes if n.get("id") == e.get("target")), "")
                if src and tgt:
                    links.append(f"{src} ↔ {tgt}")
            if links:
                return "Connections:\n" + "\n".join(links[:10])
            return "No direct connections found."
        if "central" in q or "hub" in q or "key figure" in q:
            if labels:
                return f"Most central: {', '.join(labels)}."
            return "No central figures identified."
        if "who is" in q or "tell me about" in q:
            name = q.replace("who is","").replace("tell me about","").strip().strip("?")
            match = next((n for n in accused if name and name in n.get("label","").lower()), None)
            if match:
                return f"{match['label']}: Risk {match.get('risk_tier','N/A')}, {match.get('cases',0)} case(s)."
            return f"No one matching '{name}' in the current network. Try searching for them."

        graph_ctx = self._summarize_graph(nodes, edges)
        return graph_ctx or "No network loaded. Search for a person to begin."