class ChatAgent:
    def __init__(self, chat_repo):
        self.chat_repo = chat_repo

    def process_chat_message(self, session_id: str, message: str) -> dict:
        return {"response": f"Mock response to: {message}", "session_id": session_id}
