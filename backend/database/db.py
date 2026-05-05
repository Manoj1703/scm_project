from typing import Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from backend.config import MONGODB_DB_NAME, MONGODB_URI

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def init_db() -> bool:
    global _client, _db

    client = AsyncIOMotorClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )
    database = client[MONGODB_DB_NAME]

    try:
        await client.admin.command("ping")
        await database.users.create_index("email", unique=True)
        await database.users.create_index("id", unique=True)
    except Exception:
        client.close()
        _client = None
        _db = None
        return False

    _client = client
    _db = database
    return True


async def close_db() -> None:
    global _client, _db

    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not connected.",
        )
    return _db


def get_users_collection() -> AsyncIOMotorCollection:
    return get_db()["users"]


async def ping_db() -> bool:
    if _client is None:
        return False

    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False


def is_db_connected() -> bool:
    return _db is not None
