from fastapi import FastAPI

from backend.routes.health_routes import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SCMXPertLite",
        version="0.2.0",
        description="SCMXPertLite Day 2 foundation app.",
    )
    app.include_router(health_router)
    return app


app = create_app()
