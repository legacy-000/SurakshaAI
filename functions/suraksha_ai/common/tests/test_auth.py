import sys
import os
import json
import base64
import hmac
import hashlib
import pytest
import jwt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.auth.token_manager import TokenManager
from common.auth.auth_handler import AuthHandler
from common.models.dto import LoginRequestDTO


# Helpers for testing

def _b64(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")

# Mock classes for Catalyst SDK


class MockCatalystUser:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockUserManagement:
    def __init__(self, user):
        self._user = user

    def get_current_user(self):
        return self._user


class MockCatalystApp:
    def __init__(self, user=None):
        self._user = user

    def user_management(self):
        return MockUserManagement(self._user)


def test_token_manager_generate_and_refresh():
    # Test generation
    tokens = TokenManager.generate_tokens("INV001", "Investigator", {"role_id": 1})
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["expires_in"] == 3600

    # Test refresh
    refreshed = TokenManager.refresh_access_token(tokens["refresh_token"])
    assert "access_token" in refreshed
    assert refreshed["expires_in"] == 3600


def test_token_manager_invalid_refresh():
    with pytest.raises(jwt.InvalidTokenError):
        TokenManager.refresh_access_token("invalid.refresh.token")


def test_token_manager_revocation():
    tokens = TokenManager.generate_tokens("INV001", "Investigator", {"role_id": 1})
    access_token = tokens["access_token"]

    # Decode access token to get jti
    from common.auth.token_manager import JWT_SECRET
    payload = jwt.decode(access_token, JWT_SECRET, algorithms=["HS256"], issuer="suraksha_ai")
    jti = payload["jti"]

    assert not TokenManager.is_revoked(jti)
    TokenManager.revoke_token(jti)
    assert TokenManager.is_revoked(jti)


def test_auth_handler_static_login_success():
    handler = AuthHandler()
    req = LoginRequestDTO(kgid="INV001", password="pass123")
    res = handler.login(req)
    assert "token" in res
    assert "refresh_token" in res
    assert res["user"]["kgid"] == "INV001"
    assert res["user"]["role_name"] == "Investigator"


def test_auth_handler_static_login_failure():
    handler = AuthHandler()

    # Wrong password
    req = LoginRequestDTO(kgid="INV001", password="wrong_password")
    res = handler.login(req)
    assert "error" in res
    assert res["error"] == "AUTH_001"

    # Unknown user
    req = LoginRequestDTO(kgid="UNKNOWN", password="pass123")
    res = handler.login(req)
    assert "error" in res
    assert res["error"] == "AUTH_001"


def test_auth_handler_verify_jwt_success():
    handler = AuthHandler()
    tokens = TokenManager.generate_tokens("ANL001", "Analyst", {"role_id": 2})

    uc = handler.verify_token(tokens["access_token"])
    assert uc is not None
    assert uc.kgid == "ANL001"
    assert uc.role_name == "Analyst"


def test_auth_handler_verify_jwt_revoked():
    handler = AuthHandler()
    tokens = TokenManager.generate_tokens("ANL001", "Analyst", {"role_id": 2})

    from common.auth.token_manager import JWT_SECRET
    payload = jwt.decode(tokens["access_token"], JWT_SECRET, algorithms=["HS256"], issuer="suraksha_ai")
    jti = payload["jti"]

    TokenManager.revoke_token(jti)

    uc = handler.verify_token(tokens["access_token"])
    assert uc is None


def test_auth_handler_verify_legacy_hmac():
    handler = AuthHandler()

    # Construct a legacy token
    payload_str = json.dumps({"kgid": "SUP001"})
    encoded = _b64(payload_str)
    signature = hmac.new("suraksha_ai_dev_secret_2026".encode(), encoded.encode(), hashlib.sha256).hexdigest()
    legacy_token = f"v2.{encoded}.{signature}"

    uc = handler.verify_token(legacy_token)
    assert uc is not None
    assert uc.kgid == "SUP001"
    assert uc.role_name == "Supervisor"


def test_auth_handler_verify_legacy_hmac_invalid():
    handler = AuthHandler()

    # Invalid signature
    payload_str = json.dumps({"kgid": "SUP001"})
    encoded = _b64(payload_str)
    legacy_token = f"v2.{encoded}.invalid_signature"
    uc = handler.verify_token(legacy_token)
    assert uc is None

    # Invalid layout
    uc = handler.verify_token("v2.invalidparts")
    assert uc is None


def test_auth_handler_live_user_login():
    # Setup live user
    user = MockCatalystUser(
        user_id="live_123",
        kgid="live_kgid",
        first_name="Live User",
        email="live@suraksha.ai",
        role_id=3,
        role_name="Supervisor",
        unit_id=1,
        district_id=1
    )
    app = MockCatalystApp(user)
    handler = AuthHandler(app)

    # Login should skip password check and return live user token
    req = LoginRequestDTO(kgid="ANY", password="ANY")
    res = handler.login(req)
    assert res["token"] == "catalyst_oauth"
    assert res["user"]["kgid"] == "live_kgid"
    assert res["user"]["role_name"] == "Supervisor"


def test_auth_handler_live_user_verify():
    user = MockCatalystUser(
        user_id="live_123",
        kgid="live_kgid",
        first_name="Live User",
        email="live@suraksha.ai",
        role_id=3,
        role_name="Supervisor",
        unit_id=1,
        district_id=1
    )
    app = MockCatalystApp(user)
    handler = AuthHandler(app)

    uc = handler.verify_token("any_token_string")
    assert uc is not None
    assert uc.kgid == "live_kgid"
    assert uc.role_name == "Supervisor"
