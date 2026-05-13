from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.database.db import get_db


router = APIRouter(tags=["database"])


@router.get("/ping-db")
async def ping_database(db: AsyncIOMotorDatabase = Depends(get_db)) -> dict[str, str]:
    try:
        await db.command("ping")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not connected.",
        ) from exc
    return {"db": "connected"}
