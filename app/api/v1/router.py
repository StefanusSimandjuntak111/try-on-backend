"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, models, garments, tryon, jobs

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(garments.router, prefix="/garments", tags=["garments"])
api_router.include_router(tryon.router, prefix="/tryon", tags=["tryon"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

