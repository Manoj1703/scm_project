from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION, CORS_ORIGINS
from backend.database.db import close_db, get_db, init_db
from auth.admin_seeder import seed_initial_admin
from routes.auth.admin_auth_routes import router as admin_auth_router
from backend.routes.health_routes import router as health_router
from backend.routes.info_routes import router as info_router
from backend.routes.ping_routes import router as ping_router
from backend.middleware.request_id_middleware import request_id_middleware
from core.logger import configure_logging
from routes.auth.user_auth_routes import router as user_auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_initial_admin(get_db())
    try:
        yield
    finally:
        await close_db()


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description=APP_DESCRIPTION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_id_middleware)
    app.include_router(health_router)
    app.include_router(info_router)
    app.include_router(ping_router)
    app.include_router(admin_auth_router)
    app.include_router(user_auth_router)
    return app


app = create_app()
