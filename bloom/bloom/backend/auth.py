import hmac
import os
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User

SECRET = os.getenv("JWT_SECRET", "dev-only-secret")
SERVICE_KEY = os.getenv("SERVICE_KEY", "")
bearer = HTTPBearer()


def require_service_key(x_service_key: str = Header("")):
    """Only the Streamlit server (which verified the user via OIDC) may mint tokens."""
    if not SERVICE_KEY:
        raise HTTPException(500, "SERVICE_KEY is not configured on the API")
    if not hmac.compare_digest(x_service_key, SERVICE_KEY):
        raise HTTPException(403, "Forbidden")


def make_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=1)
    return jwt.encode({"sub": str(user_id), "exp": exp}, SECRET, algorithm="HS256")


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    try:
        uid = int(jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])["sub"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Session expired, please sign in again")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "Account not found")
    return user
