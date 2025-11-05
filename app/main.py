"""FastAPI application entry point."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.router import api_router
from app.config import settings
from app.core.exceptions import TryOnException
from app.core.handlers import (
    general_exception_handler,
    sqlalchemy_exception_handler,
    tryon_exception_handler,
    validation_exception_handler,
)
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handlers
app.add_exception_handler(TryOnException, tryon_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Middleware (order matters - last added is first executed)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount static files for local storage (Colab mode)
if os.environ.get("USE_LOCAL_STORAGE", "false").lower() == "true":
    storage_path = Path("storage")
    if storage_path.exists():
        app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("Application starting up", version="0.1.0")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    from app.core.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("Application shutting down")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Try-On Backend API", "version": "0.1.0"}

