"""Job management endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.exceptions import JobNotFoundError
from app.core.logging import get_logger
from app.dependencies import get_db
from app.models.schemas import TryOnListResponse, TryOnResponse
from app.services import database

router = APIRouter()
logger = get_logger(__name__)


@router.get("", response_model=TryOnListResponse)
async def list_jobs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status_filter: Optional[str] = Query(None, description="Filter by job status"),
    model_id: Optional[UUID] = Query(None, description="Filter by model ID"),
    garment_id: Optional[UUID] = Query(None, description="Filter by garment ID"),
    db: Session = Depends(get_db),
):
    """List all try-on jobs with pagination and filtering."""
    try:
        jobs, total = database.list_jobs(
            db=db,
            skip=skip,
            limit=limit,
            status=status_filter,
            model_id=model_id,
            garment_id=garment_id,
        )
        
        return TryOnListResponse(
            jobs=[TryOnResponse.model_validate(job) for job in jobs],
            total=total,
        )
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}",
        )


@router.get("/{job_id}", response_model=TryOnResponse)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    """Get job details by ID."""
    try:
        job = database.get_job_or_404(db, job_id)
        return TryOnResponse.model_validate(job)
    except JobNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get job", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job: {str(e)}",
        )
