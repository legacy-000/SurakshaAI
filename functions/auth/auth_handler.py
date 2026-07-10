from models.dto import LoginRequestDTO, UserContextDTO, AuthorizationScopeDTO
from config.constants import ROLE_INVESTIGATOR, ROLE_ANALYST, ROLE_SUPERVISOR, ROLE_POLICYMAKER, ROLE_SYSTEM_ADMIN


class AuthHandler:
    def __init__(self):
        self._users = {}

    def login(self, req: LoginRequestDTO) -> dict:
        if not req.kgid or not req.password:
            return {"error": "AUTH_001", "message": "Invalid KGID or password."}
        user = self._authenticate(req.kgid, req.password)
        if not user:
            return {"error": "AUTH_001", "message": "Invalid KGID or password. Please try again."}
        token = self._generate_jwt(user)
        return {
            "token": token,
            "user": user.model_dump(),
            "expires_in": 3600
        }

    def _authenticate(self, kgid: str, password: str):
        from functions.auth.rbac_middleware import RBACMiddleware
        return RBACMiddleware().resolve_user(kgid)

    def _generate_jwt(self, user: UserContextDTO) -> str:
        return f"mock_jwt_{user.kgid}_{user.role_id}"

    def refresh(self, refresh_token: str) -> dict:
        return {"token": "mock_refreshed_token", "expires_in": 3600}

    def get_me(self, user_id: str) -> UserContextDTO:
        return self._users.get(user_id)
