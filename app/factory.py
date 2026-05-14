from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.core.telemetry import configure_telemetry
from app.db.session import engine


def create_app() -> FastAPI:
    """Build and configure a FastAPI application instance."""
    configure_logging()

    app = FastAPI(
        title=settings.app.name,
        openapi_url=f"{settings.api.v1_prefix}/openapi.json",
    )
    configure_telemetry(app, engine=engine)

    register_middleware(app)
    app.include_router(api_router)
    app.include_router(health_router)
    app.include_router(metrics_router)
    register_exception_handlers(app)

    return app
