from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.auth_controller import AuthController
from schemas.response import APIResponse
from schemas.requests import LoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=APIResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> APIResponse:
    controller = AuthController(db)
    return controller.login(body.username, body.password_hash)
