from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.config import get_settings
from backend.database.db import get_db


router = APIRouter(tags=["info"])


@router.get("/info")
async def info(
    settings = Depends(get_settings),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict[str, str]:
    _ = db
    return {
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }
