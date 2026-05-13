from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from backend.database.db import close_db, init_db
from backend.routes.health_routes import router as health_router
from backend.routes.ping_routes import router as ping_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        yield
    finally:
        await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(ping_router)
    return app


app = create_app()
