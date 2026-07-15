import hashlib, hmac, json, base64, logging
from datetime import datetime
from typing import Optional
from models.dto import LoginRequestDTO, UserContextDTO

logger = logging.getLogger(__name__)

USERS = {
    "INV001": {"password_hash": "mock_hash", "role_name": "Investigator", "role_id": 1, "unit_id": 1, "district_id": 1, "name": "Ravi Kumar"},
    "ANL001": {"password_hash": "mock_hash", "role_name": "Analyst", "role_id": 2, "district_id": 18, "name": "Priya Sharma"},
    "SUP001": {"password_hash": "mock_hash", "role_name": "Supervisor", "role_id": 3, "unit_id": 1, "district_id": 1, "name": "Amit Singh"},
    "POL001": {"password_hash": "mock_hash", "role_name": "Policymaker", "role_id": 4, "district_id": 18, "name": "Dr. Meena Rao"},
    "ADM001": {"password_hash": "mock_hash", "role_name": "System Administrator", "role_id": 5, "name": "Vikram P"},
    "TSE001": {"password_hash": "mock_hash", "role_name": "Technical Support Engineer", "role_id": 6, "name": "Anita Rao"},
}

MOCK_SECRET = "suraksha_ai_dev_secret_2026"


def _b64(data: str) -> str:
    return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")

def _unb64(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode()).decode()


class AuthHandler:
    def __init__(self, catalyst_app=None):
        self._catalyst_app = catalyst_app

    def _live_user(self) -> Optional[dict]:
        """Get current user from Catalyst User Management when live."""
        if not self._catalyst_app:
            return None
        try:
            um = self._catalyst_app.user_management()
            current = um.get_current_user()
            if current:
                user_id = str(getattr(current, 'user_id', ''))
                kgid = str(getattr(current, 'kgid', getattr(current, 'email', user_id)))
                return {
                    "user_id": kgid,
                    "kgid": kgid,
                    "first_name": getattr(current, 'first_name', '') or getattr(current, 'name', ''),
                    "email": getattr(current, 'email', ''),
                    "role_id": getattr(current, 'role_id', 1) if hasattr(current, 'role_id') else 1,
                    "role_name": getattr(current, 'role_name', 'Investigator') if hasattr(current, 'role_name') else 'Investigator',
                    "unit_id": getattr(current, 'unit_id', None) if hasattr(current, 'unit_id') else None,
                    "district_id": getattr(current, 'district_id', None) if hasattr(current, 'district_id') else None,
                }
        except Exception as e:
            logger.info("Catalyst User Management not available: %s", e)
        return None

    def login(self, req: LoginRequestDTO) -> dict:
        # Try Catalyst OAuth first
        live_user = self._live_user()
        if live_user:
            return {"token": "catalyst_oauth", "user": live_user, "expires_in": 3600}

        # Fallback to static user map
        user = USERS.get(req.kgid.upper())
        if not user or req.password != "pass123":
            return {"error": "AUTH_001", "message": "Invalid KGID or password."}
        now = datetime.now().isoformat()
        payload = json.dumps({"kgid": req.kgid.upper(), "role": user["role_name"], "iat": now})
        encoded = _b64(payload)
        sig = hmac.new(MOCK_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        token = f"v2.{encoded}.{sig}"
        return {"token": token, "user": {
            "user_id": req.kgid.upper(), "kgid": req.kgid.upper(),
            "first_name": user["name"], "role_id": user["role_id"],
            "role_name": user["role_name"], "unit_id": user.get("unit_id"),
            "district_id": user.get("district_id"),
        }, "expires_in": 3600}

    def verify_token(self, token: str) -> Optional[UserContextDTO]:
        # Try Catalyst OAuth user
        live_user = self._live_user()
        if live_user:
            return UserContextDTO(**live_user, language_preference="en")

        # Fallback to mock JWT
        try:
            parts = token.split(".")
            if len(parts) != 3 or parts[0] != "v2":
                return None
            encoded = parts[1]
            expected_sig = hmac.new(MOCK_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
            if parts[2] != expected_sig:
                return None
            payload = _unb64(encoded)
            data = json.loads(payload)
            user = USERS.get(data["kgid"])
            if not user:
                return None
            return UserContextDTO(
                user_id=data["kgid"], kgid=data["kgid"], first_name=user["name"],
                email="", role_id=user["role_id"], role_name=user["role_name"],
                unit_id=user.get("unit_id"), district_id=user.get("district_id"),
                language_preference="en",
            )
        except Exception:
            return None
