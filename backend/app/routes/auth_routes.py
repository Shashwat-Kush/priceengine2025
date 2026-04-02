from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.db.mongo import get_database
from app.utils.auth import create_token, hash_password, verify_password
from app.utils.helpers import default_seed_payload, utc_now

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=6)
    organization_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6)


class UpdateProfileRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    organization_name: str = Field(min_length=2, max_length=120)


def _auth_user_payload(user: dict, org: dict | None) -> dict:
    return {
        "id": str(user.get("_id", "")),
        "name": str(user.get("name", "")),
        "email": str(user.get("email", "")),
        "orgId": str(user.get("org_id", "")),
        "organizationName": str(org.get("name", "")) if org else "",
    }


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    email = payload.email.strip().lower()
    name = (payload.name or email.split("@")[0]).strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    now = utc_now()
    org_id = f"org-{uuid4().hex[:12]}"
    user_id = f"user-{uuid4().hex[:12]}"

    org_doc = {
        "_id": org_id,
        "name": payload.organization_name.strip(),
        "created_at": now,
        "updated_at": now,
    }
    user_doc = {
        "_id": user_id,
        "org_id": org_id,
        "name": name,
        "email": email,
        "password_hash": hash_password(payload.password),
        "created_at": now,
        "updated_at": now,
    }

    await db.organizations.insert_one(org_doc)
    await db.users.insert_one(user_doc)

    try:
        sample_payload = default_seed_payload(org_id=org_id)
        for collection_name, docs in sample_payload.items():
            if docs:
                await db[collection_name].insert_many(docs)
    except Exception as exc:
        await db.users.delete_one({"_id": user_id})
        await db.organizations.delete_one({"_id": org_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize organization sample data",
        ) from exc

    return {
        "token": create_token(user_doc),
        "user": _auth_user_payload(user_doc, org_doc),
    }


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    email = payload.email.strip().lower()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    password_hash = str(user.get("password_hash", ""))
    valid = verify_password(payload.password, password_hash)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    org = await db.organizations.find_one({"_id": user.get("org_id")})

    return {
        "token": create_token(user),
        "user": _auth_user_payload(user, org),
    }


@router.get("/me")
async def me(
    current_user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    org = await db.organizations.find_one({"_id": current_user.get("org_id")})
    return _auth_user_payload(current_user, org)


@router.put("/me")
async def update_me(
    payload: UpdateProfileRequest,
    current_user=Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    name = payload.name.strip()
    email = payload.email.strip().lower()
    organization_name = payload.organization_name.strip()

    existing_user = await db.users.find_one({"email": email})
    if existing_user and str(existing_user.get("_id", "")) != str(current_user.get("_id", "")):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    now = utc_now()
    await db.users.update_one(
        {"_id": current_user.get("_id")},
        {
            "$set": {
                "name": name,
                "email": email,
                "updated_at": now,
            }
        },
    )
    await db.organizations.update_one(
        {"_id": current_user.get("org_id")},
        {
            "$set": {
                "name": organization_name,
                "updated_at": now,
            }
        },
    )

    updated_user = await db.users.find_one({"_id": current_user.get("_id")})
    updated_org = await db.organizations.find_one({"_id": current_user.get("org_id")})
    if not updated_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh user profile")

    return {
        "token": create_token(updated_user),
        "user": _auth_user_payload(updated_user, updated_org),
    }


@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    _ = current_user
    return {"success": True}
