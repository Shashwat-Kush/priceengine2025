import os
from typing import Optional

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


def _mongo_uri() -> str:
    uri = os.getenv("MONGODB_URI", "").strip()
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Set it via an environment variable or in backend/.env. "
            "Example (Atlas): mongodb+srv://<user>:<password>@<cluster>.mongodb.net/ai_pricing_engine?retryWrites=true&w=majority"
        )
    return uri


def _mongo_db_name() -> Optional[str]:
    name = os.getenv("MONGODB_DB", "").strip()
    return name or None


def _resolve_database(client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    explicit_db = _mongo_db_name()
    if explicit_db:
        return client[explicit_db]

    try:
        default_db = client.get_default_database()
        if default_db is not None:
            return default_db
    except Exception:
        pass

    return client["ai_pricing_engine"]


async def connect_to_mongo() -> None:
    global _client, _database
    if _client is not None:
        return

    _client = AsyncIOMotorClient(_mongo_uri(), serverSelectionTimeoutMS=5000)
    _database = _resolve_database(_client)
    await _database.command("ping")


async def close_mongo_connection() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None


async def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise HTTPException(status_code=500, detail="Database is not initialized")
    return _database
