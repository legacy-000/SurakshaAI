from functions.chat.chat_handler import ChatHandler
from functions.sql.query_executor import QueryExecutor
from models.dto import QueryRequestDTO, UserContextDTO

def test_empty_query():
    handler = ChatHandler()
    user = UserContextDTO(user_id="INV001", kgid="INV001", first_name="Test",
                          email="t@t.com", role_id=1, role_name="Investigator")
    req = QueryRequestDTO(message="")
    resp = handler.handle_query(req, user)
    assert resp is not None

def test_invalid_sql():
    executor = QueryExecutor()
    result = executor.execute("INVALID SQL HERE")
    assert "error" in result or result.get("execution_status") == "success"
