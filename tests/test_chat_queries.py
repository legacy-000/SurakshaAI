from functions.chat.chat_handler import ChatHandler
from models.dto import QueryRequestDTO, UserContextDTO

def test_simple_query():
    handler = ChatHandler()
    user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Test",
                          email="t@t.com", role_id=1, role_name="Investigator")
    req = QueryRequestDTO(message="Theft cases in Bangalore this year")
    resp = handler.handle_query(req, user)
    assert resp.content_text is not None
    assert resp.message_type == "ai_response"

def test_query_with_context():
    handler = ChatHandler()
    user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Test",
                          email="t@t.com", role_id=1, role_name="Investigator")
    req1 = QueryRequestDTO(message="Show murder cases in Mysuru")
    resp1 = handler.handle_query(req1, user)
    req2 = QueryRequestDTO(message="Which had arrests?", conversation_id=resp1.conversation_id)
    resp2 = handler.handle_query(req2, user)
    assert resp2.content_text is not None
