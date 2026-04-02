from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongo import get_database
from app.utils.auth import verify_token


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1].strip()
    return token or None


async def _resolve_user_from_token(token: str, db: AsyncIOMotorDatabase) -> dict:
    try:
        payload = verify_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = str(payload.get("sub", "")).strip()
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def get_optional_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    token = _extract_bearer_token(authorization)
    if not token:
        return None

    return await _resolve_user_from_token(token, db)


async def get_current_user(
    optional_user=Depends(get_optional_current_user),
):
    if optional_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return optional_user
