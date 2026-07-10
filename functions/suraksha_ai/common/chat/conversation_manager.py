import uuid
from datetime import datetime
from common.models.dto import ConversationDTO, ConversationMessageDTO


class ConversationManager:
    def __init__(self):
        self._conversations = {}
        self._messages = {}

    def create_conversation(self, user_id: str, title: str = "New Conversation",
                            language_code: str = "en") -> ConversationDTO:
        conv_id = str(uuid.uuid4())
        conv = ConversationDTO(
            conversation_id=conv_id, title=title,
            language_code=language_code, created_at=datetime.now().isoformat()
        )
        self._conversations[conv_id] = conv
        self._messages[conv_id] = []
        return conv

    def get_conversation(self, conversation_id: str) -> ConversationDTO:
        return self._conversations.get(conversation_id)

    def list_conversations(self, user_id: str) -> list[ConversationDTO]:
        return [c for c in self._conversations.values()
                if hasattr(c, 'user_id') and c.user_id == user_id]

    def add_message(self, conversation_id: str, message: ConversationMessageDTO):
        if conversation_id not in self._messages:
            self._messages[conversation_id] = []
        self._messages[conversation_id].append(message)
        conv = self._conversations.get(conversation_id)
        if conv:
            conv.updated_at = datetime.now().isoformat()

    def get_context(self, conversation_id: str, limit: int = 10) -> list[ConversationMessageDTO]:
        msgs = self._messages.get(conversation_id, [])
        return msgs[-limit:]

    def archive_conversation(self, conversation_id: str) -> bool:
        conv = self._conversations.get(conversation_id)
        if conv:
            conv.is_archived = True
            return True
        return False

    def delete_conversation(self, conversation_id: str) -> bool:
        self._messages.pop(conversation_id, None)
        return self._conversations.pop(conversation_id, None) is not None
