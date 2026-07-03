from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from configuration.database import get_db
from controllers.auth_controller import AuthController
from schemas.response import APIResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=APIResponse)
def login(username: str, password_hash: str, db: Session = Depends(get_db)) -> APIResponse:
    # Controller Layer is invoked
    controller = AuthController(db)
    return controller.login(username, password_hash)
