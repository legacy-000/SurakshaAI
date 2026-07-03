import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Simulated creation of secure JWT token for authenticated police officers.
    """
    # Placeholder return
    return "simulated_jwt_token_hash"

def decode_access_token(token: str) -> Dict[str, Any] | None:
    """
    Simulated token decryption and claim verification.
    """
    # Placeholder return
    if token == "simulated_jwt_token_hash":
        return {"sub": "officer_username", "role": "officer"}
    return None
