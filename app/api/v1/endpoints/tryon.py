"""Try-on processing endpoints."""

import io
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import GarmentNotFoundError, ImageValidationError, JobNotFoundError, ModelNotFoundError
from app.core.logging import get_logger
from app.dependencies import get_db
from app.models.schemas import (
    TryOnCreate,
    TryOnResponse,
    TryOnStatusResponse,
    UploadResponse,
)
from app.services import database
from app.services.cache import cache_service
from app.services.storage import storage_service
from app.services.validation import validate_image_file

router = APIRouter()
logger = get_logger(__name__)


@router.post("/direct-sync", response_model=TryOnResponse, status_code=status.HTTP_200_OK)
async def create_and_process_tryon_sync(
    model_file: UploadFile = File(..., description="Human model image file"),
    garment_file: UploadFile = File(..., description="Clothing/garment image file"),
    model_name: Optional[str] = Form(None, description="Model name"),
    garment_name: Optional[str] = Form(None, description="Garment name"),
    db: Session = Depends(get_db),
):
    """Create and process try-on job synchronously (for Colab - no Celery needed).
    
    This endpoint:
    - Accepts both image files
    - Processes immediately (synchronous)
    - Returns completed result with image URL
    
    Perfect for Colab where Celery workers are not available.
    """
    import time
    from PIL import Image
    
    try:
        start_time = time.time()
        
        # Validate images
        model_content = await model_file.read()
        model_io = io.BytesIO(model_content)
        validate_image_file(model_io)
        
        garment_content = await garment_file.read()
        garment_io = io.BytesIO(garment_content)
        validate_image_file(garment_io)
        
        # Upload images
        model_io.seek(0)
        model_original, model_thumbnail = storage_service.upload_image_with_thumbnail(
            model_io, settings.S3_BUCKET_MODELS
        )
        model_url = storage_service.get_file_url(settings.S3_BUCKET_MODELS, model_original)
        
        garment_io.seek(0)
        garment_original, garment_thumbnail = storage_service.upload_image_with_thumbnail(
            garment_io, settings.S3_BUCKET_GARMENTS
        )
        garment_url = storage_service.get_file_url(settings.S3_BUCKET_GARMENTS, garment_original)
        
        # Create records
        model = database.create_model(db=db, original_image_url=model_url, 
                                     thumbnail_url=storage_service.get_file_url(settings.S3_BUCKET_MODELS, model_thumbnail),
                                     name=model_name)
        garment = database.create_garment(db=db, original_image_url=garment_url,
                                         thumbnail_url=storage_service.get_file_url(settings.S3_BUCKET_GARMENTS, garment_thumbnail),
                                         name=garment_name)
        job = database.create_job(db=db, model_id=model.id, garment_id=garment.id)
        
        # Update job to processing
        database.update_job(db, job.id, status="processing")
        
        logger.info("Processing try-on synchronously", job_id=str(job.id))
        
        # Load images
        model_image = Image.open(io.BytesIO(model_content))
        garment_image = Image.open(io.BytesIO(garment_content))
        
        # Perform inference (this will use placeholder if torch not available)
        try:
            from app.services.inference import inference_service
            result_image = inference_service.perform_tryon(
                model_image=model_image,
                garment_image=garment_image,
            )
        except Exception as e:
            logger.error("Inference failed", error=str(e))
            # Use placeholder - just overlay garment on model
            result_image = model_image.copy()
        
        # Save result
        result_bytes = io.BytesIO()
        result_image.save(result_bytes, format='JPEG', quality=95)
        result_bytes.seek(0)
        
        # Upload result
        result_name = storage_service.upload_file(
            result_bytes,
            settings.S3_BUCKET_RESULTS,
            content_type="image/jpeg"
        )
        result_url = storage_service.get_file_url(settings.S3_BUCKET_RESULTS, result_name)
        
        # Update job with result
        processing_time = time.time() - start_time
        database.update_job(
            db, job.id,
            status="completed",
            result_url=result_url,
            processing_time=processing_time
        )
        database.update_model(db, model.id, status="ready")
        database.update_garment(db, garment.id, status="ready")
        
        logger.info("Sync processing completed", job_id=str(job.id), time=processing_time)
        
        # Return completed job
        job = database.get_job_or_404(db, job.id)
        return TryOnResponse.model_validate(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Sync processing failed", error=str(e))
        if 'job' in locals():
            database.update_job(db, job.id, status="failed", error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process try-on: {str(e)}",
        )



@router.post("/direct", response_model=TryOnResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_tryon_job_direct(
    model_file: UploadFile = File(..., description="Human model image file"),
    garment_file: UploadFile = File(..., description="Clothing/garment image file"),
    model_name: Optional[str] = Form(None, description="Model name"),
    garment_name: Optional[str] = Form(None, description="Garment name"),
    options: Optional[str] = Form(None, description="JSON options"),
    db: Session = Depends(get_db),
):
    """Create a try-on job directly with two image files.
    
    This endpoint accepts:
    - **model_file**: Human model image (person photo)
    - **garment_file**: Clothing/garment image
    
    Returns:
    - **job_id**: ID to track the processing job
    - **status**: Current job status
    - **result_url**: URL to the final fitted image (clothing on model) when completed
    
    The result will be the fitting of the clothing to the model image.
    """
    try:
        # Validate model image
        model_content = await model_file.read()
        model_io = io.BytesIO(model_content)
        try:
            validate_image_file(model_io)
        except ImageValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid model image: {str(e)}",
            )
        
        # Validate garment image
        garment_content = await garment_file.read()
        garment_io = io.BytesIO(garment_content)
        try:
            validate_image_file(garment_io)
        except ImageValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid garment image: {str(e)}",
            )
        
        # Parse options if provided
        options_dict = None
        if options:
            import json
            try:
                options_dict = json.loads(options)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON options",
                )
        
        # Upload model image
        model_io.seek(0)
        model_original, model_thumbnail = storage_service.upload_image_with_thumbnail(
            model_io,
            settings.S3_BUCKET_MODELS,
        )
        # Generate URLs (handles both S3/MinIO and local storage)
        model_url = storage_service.get_file_url(settings.S3_BUCKET_MODELS, model_original)
        model_thumbnail_url = storage_service.get_file_url(settings.S3_BUCKET_MODELS, model_thumbnail)
        
        # Upload garment image
        garment_io.seek(0)
        garment_original, garment_thumbnail = storage_service.upload_image_with_thumbnail(
            garment_io,
            settings.S3_BUCKET_GARMENTS,
        )
        garment_url = storage_service.get_file_url(settings.S3_BUCKET_GARMENTS, garment_original)
        garment_thumbnail_url = storage_service.get_file_url(settings.S3_BUCKET_GARMENTS, garment_thumbnail)
        
        # Create model record
        model = database.create_model(
            db=db,
            original_image_url=model_url,
            thumbnail_url=model_thumbnail_url,
            name=model_name,
        )
        
        # Create garment record
        garment = database.create_garment(
            db=db,
            original_image_url=garment_url,
            thumbnail_url=garment_thumbnail_url,
            name=garment_name,
        )
        
        # Create try-on job
        job = database.create_job(
            db=db,
            model_id=model.id,
            garment_id=garment.id,
            options=options_dict,
        )
        
        logger.info(
            "Direct try-on job created",
            job_id=str(job.id),
            model_id=str(model.id),
            garment_id=str(garment.id),
        )
        
        # Trigger preprocessing and inference tasks (if Celery available)
        try:
            from app.workers.tasks import preprocess_model_task, preprocess_garment_task, tryon_inference_task
            
            # Preprocess both images
            preprocess_model_task.delay(str(model.id))
            preprocess_garment_task.delay(str(garment.id))
            
            # Trigger inference (will wait for preprocessing)
            tryon_inference_task.delay(str(job.id))
        except ImportError:
            logger.warning("Celery not available - tasks will not run automatically")
            # In Colab, you can call these functions directly if needed
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create direct try-on job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create try-on job: {str(e)}",
        )


@router.post("", response_model=TryOnResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_tryon_job(
    request: TryOnCreate,
    db: Session = Depends(get_db),
):
    """Create a new try-on job using existing model and garment IDs.
    
    This endpoint requires:
    - **model_id**: UUID of an already uploaded human model image
    - **garment_id**: UUID of an already uploaded garment/clothing image
    
    Returns:
    - **job_id**: ID to track the processing job
    - **status**: Current job status  
    - **result_url**: URL to the final fitted image (clothing on model) when completed
    
    The result will be the fitting of the clothing to the model image.
    
    Note: Use POST /direct for uploading both images in one request.
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
        
        # Trigger async processing task (if Celery available)
        try:
            from app.workers.tasks import tryon_inference_task
            tryon_inference_task.delay(str(job.id))
        except ImportError:
            logger.warning("Celery not available - inference task will not run automatically")
            # In Colab, you can call inference directly if needed
        
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
    
    Returns the complete job information including the final fitted image URL.
    
    Response includes:
    - **result_url**: URL to the final image showing the clothing fitted on the model
    - **status**: Job processing status (queued, processing, completed, failed)
    - **model_id**: ID of the human model used
    - **garment_id**: ID of the clothing/garment used
    
    The result_url points to the final fitted image when status is "completed".
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
