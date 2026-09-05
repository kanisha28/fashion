import os
import hashlib
import hmac
import datetime
from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User

SECRET_KEY = os.getenv("SECRET_KEY", "fashion-forecast-secret-key-change-in-production-2026")
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a password securely using PBKDF2-HMAC-SHA256 with salt."""
    salt = "fashion_retail_salt_2026".encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return key.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored hash."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def create_access_token(user_id: int, username: str, role: str) -> str:
    """Creates a token containing user identity and unix epoch expiry."""
    expiry_ts = int(datetime.datetime.utcnow().timestamp()) + 86400
    raw = f"{user_id}:{username}:{role}:{expiry_ts}"
    sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw}:{sig}"


def decode_access_token(token: str) -> Optional[dict]:
    """Decodes and validates a session/bearer token."""
    try:
        parts = token.split(":")
        if len(parts) != 5:
            return None
        user_id, username, role, expiry_ts_str, sig = parts
        raw = f"{user_id}:{username}:{role}:{expiry_ts_str}"
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        expiry_ts = int(expiry_ts_str)
        if int(datetime.datetime.utcnow().timestamp()) > expiry_ts:
            return None
        return {"user_id": int(user_id), "username": username, "role": role}
    except Exception:
        return None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency to extract and authenticate current user from Bearer header."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with token not found",
        )
    return user


def require_role(allowed_roles: List[str]):
    """Decorator / dependency returning user only if role matches allowed roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_roles}, your role: {current_user.role}",
            )
        return current_user
    return role_checker
