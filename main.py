from fastapi import FastAPI

from backend.config import APP_HOST, APP_PORT
from backend.database.db import close_db, init_db
from backend.routes.health_routes import router as health_router
from backend.routes.user_routes import router as user_router


app = FastAPI(
    title="SCM Project API",
    version="0.1.0",
    description="Backend API for the SCM project.",
)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "message": "SCM API is running",
        "health": "/health",
        "signup": "/signup",
        "login": "/login",
        "me": "/me",
    }


app.include_router(health_router)
app.include_router(user_router)


@app.on_event("startup")
async def startup_event() -> None:
    await init_db()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_db()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=False)
