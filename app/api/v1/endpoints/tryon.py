"""Try-on processing endpoints."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.exceptions import GarmentNotFoundError, JobNotFoundError, ModelNotFoundError
from app.core.logging import get_logger
from app.dependencies import get_db
from app.models.schemas import (
    TryOnCreate,
    TryOnResponse,
    TryOnStatusResponse,
)
from app.services import cache_service, database, storage_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("", response_model=TryOnResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_tryon_job(
    request: TryOnCreate,
    db: Session = Depends(get_db),
):
    """Create a new try-on job.

    The job will be queued for processing. Use the job_id to check status and retrieve results.
    """
    try:
        # Validate model exists
        model = database.get_model_or_404(db, request.model_id)
        if model.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Model {request.model_id} is not ready (status: {model.status})",
            )
        
        # Validate garment exists
        garment = database.get_garment_or_404(db, request.garment_id)
        if garment.status != "ready":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Garment {request.garment_id} is not ready (status: {garment.status})",
            )
        
        # Create job
        job = database.create_job(
            db=db,
            model_id=request.model_id,
            garment_id=request.garment_id,
            options=request.options.dict() if request.options else None,
        )
        
        logger.info("Try-on job created", job_id=str(job.id), model_id=str(request.model_id), garment_id=str(request.garment_id))
        
        # Trigger async processing task
        from app.workers.tasks import tryon_inference_task
        tryon_inference_task.delay(str(job.id))
        
        # Cache job status
        cache_service.set_json(
            f"job:{job.id}",
            {
                "status": job.status,
                "created_at": job.created_at.isoformat(),
            },
            ttl=3600,
        )
        
        return TryOnResponse.model_validate(job)
        
    except (ModelNotFoundError, GarmentNotFoundError):
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create try-on job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create try-on job: {str(e)}",
        )


@router.get("/{job_id}", response_model=TryOnResponse)
async def get_tryon_result(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    """Get try-on job result.

    Returns the complete job information including result URL if processing is complete.
    """
    try:
        job = database.get_job_or_404(db, job_id)
        
        # Generate presigned URL if result exists
        result_url = job.result_url
        if result_url and settings.S3_ENDPOINT:
            try:
                # Extract bucket and object name from URL
                if settings.S3_BUCKET_RESULTS in result_url:
                    object_name = result_url.split("/")[-1]
                    result_url = storage_service.get_presigned_url(
                        settings.S3_BUCKET_RESULTS,
                        object_name,
                        expiration=3600,  # 1 hour
                    )
            except Exception as e:
                logger.warning("Failed to generate presigned URL", error=str(e))
        
        # Create response with updated URL
        response_data = TryOnResponse.model_validate(job)
        if result_url != job.result_url:
            response_data.result_url = result_url
        return response_data
        
    except JobNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get try-on result", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get try-on result: {str(e)}",
        )


@router.get("/{job_id}/status", response_model=TryOnStatusResponse)
async def get_job_status(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    """Get try-on job status.

    Returns current status and estimated completion time if available.
    """
    try:
        # Try cache first
        cached = cache_service.get_json(f"job:{job_id}")
        if cached:
            return TryOnStatusResponse(
                id=job_id,
                status=cached.get("status", "unknown"),
                error_message=None,
                estimated_time=None,
                progress=None,
                created_at=datetime.fromisoformat(cached.get("created_at", datetime.utcnow().isoformat())),
                completed_at=None,
            )
        
        # Get from database
        job = database.get_job_or_404(db, job_id)
        
        # Calculate estimated time based on status
        estimated_time = None
        progress = None
        
        if job.status == "queued":
            estimated_time = 30  # Estimate 30 seconds
            progress = 0.0
        elif job.status == "processing":
            estimated_time = 15  # Estimate 15 seconds remaining
            progress = 50.0
        elif job.status == "completed":
            progress = 100.0
        elif job.status == "failed":
            progress = 0.0
        
        return TryOnStatusResponse(
            id=job.id,
            status=job.status,
            error_message=job.error_message,
            estimated_time=estimated_time,
            progress=progress,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
        
    except JobNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}",
        )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    """Cancel or delete a try-on job.

    Only jobs in 'queued' or 'processing' status can be cancelled.
    Completed or failed jobs will be deleted.
    """
    try:
        job = database.get_job_or_404(db, job_id)
        
        # Check if job can be cancelled
        if job.status in ("queued", "processing"):
            # Update status to cancelled
            database.update_job(
                db=db,
                job_id=job_id,
                status="cancelled",
            )
            logger.info("Job cancelled", job_id=str(job_id))
        else:
            # Delete completed/failed jobs
            # Delete result file if exists
            if job.result_url:
                try:
                    object_name = job.result_url.split("/")[-1]
                    storage_service.delete_file(settings.S3_BUCKET_RESULTS, object_name)
                except Exception as e:
                    logger.warning("Failed to delete result file", error=str(e))
            
            database.delete_job(db, job_id)
            logger.info("Job deleted", job_id=str(job_id))
        
        # Clear cache
        cache_service.delete(f"job:{job_id}")
        
        return None
        
    except JobNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to cancel/delete job", job_id=str(job_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}",
        )
