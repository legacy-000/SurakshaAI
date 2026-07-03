from sqlalchemy.orm import Session
from services.auth_service import AuthService
from schemas.response import APIResponse

class AuthController:
    def __init__(self, db: Session):
        self.auth_service = AuthService(db)

    def login(self, username: str, password_hash: str) -> APIResponse:
        data = self.auth_service.authenticate_user(username, password_hash)
        return APIResponse(
            status="Project Initialized",
            message="User authenticated successfully by Auth Controller-Service-Repository flow",
            data=data
        )
