import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
import jwt

JWT_ALGORITHM = "HS256"


def _jwt_expires_hours() -> int:
    value = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
    return max(1, value)


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET is not set. Configure it in backend/.env or environment variables.")
    return secret


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    hashed = bcrypt.hashpw(encoded, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user: Dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    expires_hours = _jwt_expires_hours()
    payload = {
        "sub": str(user.get("_id")),
        "org_id": str(user.get("org_id", "")),
        "email": str(user.get("email", "")),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_hours)).timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
