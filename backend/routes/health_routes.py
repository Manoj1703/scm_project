from fastapi import APIRouter

from backend.database.db import ping_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    database_ok = await ping_db()
    return {
        "status": "ok",
        "database": "connected" if database_ok else "disconnected",
    }
