"""
PayShield AI FastAPI Application Entry Point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.logging import setup_logging
from app.database import init_db, close_db
from app.cache import init_cache, close_cache
from app.ml.model_loader import model_registry
from app.middleware import (
    add_cors_middleware,
    RequestIdMiddleware,
    RequestLoggingMiddleware,
)
from app.exceptions import (
    PayShieldException,
    payshield_exception_handler,
    general_exception_handler,
)
from app.api import health, predictions, transactions, users

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting PayShield AI ({settings.APP_VERSION})")
    logger.info(f"Environment: {settings.ENV}")

    try:
        await init_db()
        await init_cache()
        model_registry.load_model()
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down PayShield AI")
    await close_db()
    await close_cache()
    logger.info("All services closed successfully")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Real-time, explainable transaction risk detection for modern finance",
    lifespan=lifespan,
)

# Add middlewares
add_cors_middleware(app)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIdMiddleware)

# Exception handlers
app.add_exception_handler(PayShieldException, payshield_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router)
app.include_router(predictions.router)
app.include_router(transactions.router)
app.include_router(users.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENV,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=1 if settings.DEBUG else settings.WORKERS,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )