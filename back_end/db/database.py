from typing import Optional

from fastapi import Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from back_end.config import settings


class MongoSingleton:
    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> AsyncIOMotorDatabase:
        if self._client is not None and self._db is not None:
            return self._db

        client = AsyncIOMotorClient(
            settings.MONGO_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        database = client[settings.DB_NAME]

        try:
            await client.admin.command("ping")
            indexes = await database.users.index_information()
            if "id_1" in indexes:
                await database.users.drop_index("id_1")
            await database.users.create_index("email", unique=True)
        except Exception as exc:
            client.close()
            raise RuntimeError("Unable to connect to MongoDB.") from exc

        self._client = client
        self._db = database
        return database

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
        self._client = None
        self._db = None

    def get_db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database is not connected.",
            )
        return self._db

    async def ping(self) -> bool:
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False


mongo = MongoSingleton()


async def init_db() -> bool:
    await mongo.connect()
    return True


async def close_db() -> None:
    await mongo.close()


def get_db() -> AsyncIOMotorDatabase:
    return mongo.get_db()


def get_users_collection() -> AsyncIOMotorCollection:
    return get_db()["users"]


async def ping_db() -> bool:
    return await mongo.ping()


def is_db_connected() -> bool:
    try:
        mongo.get_db()
    except HTTPException:
        return False
    return True


def db_dependency() -> AsyncIOMotorDatabase:
    return get_db()
