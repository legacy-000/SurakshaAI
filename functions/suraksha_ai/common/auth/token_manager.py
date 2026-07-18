import os
import uuid
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Set
import jwt

logger = logging.getLogger(__name__)

MOCK_SECRET = "suraksha_ai_dev_secret_2026"
MOCK_REFRESH_SECRET = "suraksha_ai_refresh_secret_2026"

JWT_SECRET = os.environ.get("SURAKSHA_JWT_SECRET", MOCK_SECRET)
REFRESH_SECRET = os.environ.get("SURAKSHA_REFRESH_SECRET", MOCK_REFRESH_SECRET)

_revoked_tokens: Set[str] = set()
_lock = threading.Lock()


class TokenManager:
    @staticmethod
    def generate_tokens(user_id: str, role: str, additional_claims: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate access and refresh tokens for a user.

        Access token expires in 1 hour.
        Refresh token expires in 7 days.
        """
        now = datetime.utcnow()
        access_jti = str(uuid.uuid4())

        access_payload = {
            "kgid": user_id,
            "role": role,
            "jti": access_jti,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "iss": "suraksha_ai"
        }
        if additional_claims:
            access_payload.update(additional_claims)

        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm="HS256")

        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            "kgid": user_id,
            "role": role,
            "jti": refresh_jti,
            "iat": now,
            "exp": now + timedelta(days=7),
            "iss": "suraksha_ai"
        }
        refresh_token = jwt.encode(refresh_payload, REFRESH_SECRET, algorithm="HS256")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": 3600
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """Verify refresh token and issue a new access token."""
        try:
            payload = jwt.decode(refresh_token, REFRESH_SECRET, algorithms=["HS256"], issuer="suraksha_ai")
            jti = payload.get("jti")

            if jti and TokenManager.is_revoked(jti):
                raise jwt.InvalidTokenError("Token has been revoked")

            kgid = payload.get("kgid")
            role = payload.get("role")

            if not kgid or not role:
                raise jwt.InvalidTokenError("Invalid token payload")

            # Issue new access token
            now = datetime.utcnow()
            access_jti = str(uuid.uuid4())
            access_payload = {
                "kgid": kgid,
                "role": role,
                "jti": access_jti,
                "iat": now,
                "exp": now + timedelta(hours=1),
                "iss": "suraksha_ai"
            }

            access_token = jwt.encode(access_payload, JWT_SECRET, algorithm="HS256")
            return {
                "access_token": access_token,
                "expires_in": 3600
            }
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token signature expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid refresh token: %s", e)
            raise

    @staticmethod
    def revoke_token(jti: str) -> None:
        """Revoke a token by adding its jti to the revoked list."""
        with _lock:
            _revoked_tokens.add(jti)
            logger.info("Token with jti %s revoked successfully", jti)

    @staticmethod
    def is_revoked(jti: str) -> bool:
        """Check if token's jti is in the revoked list."""
        with _lock:
            return jti in _revoked_tokens
