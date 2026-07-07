from functions.auth.auth_handler import AuthHandler
from models.dto import LoginRequestDTO

def test_login_success():
    handler = AuthHandler()
    req = LoginRequestDTO(kgid="INV001", password="test")
    result = handler.login(req)
    assert "token" in result
    assert result["user"]["role_id"] == 1

def test_login_invalid():
    handler = AuthHandler()
    req = LoginRequestDTO(kgid="INVALID", password="wrong")
    result = handler.login(req)
    assert "error" in result
