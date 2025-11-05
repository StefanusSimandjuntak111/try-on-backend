"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import setup_logging

# Setup logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


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

