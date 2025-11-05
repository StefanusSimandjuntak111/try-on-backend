"""Garment management endpoints."""

import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import GarmentNotFoundError, ImageValidationError
from app.core.logging import get_logger
from app.dependencies import get_db
from app.models.schemas import GarmentListResponse, GarmentResponse, UploadResponse
from app.services import database
from app.services.cache import cache_service
from app.services.storage import storage_service
from app.services.validation import validate_image_file

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_garment(
    file: UploadFile = File(..., description="Garment image file"),
    name: Optional[str] = Form(None, description="Garment name"),
    metadata: Optional[str] = Form(None, description="JSON metadata"),
    db: Session = Depends(get_db),
):
    """Upload garment image.

    The image will be validated, uploaded to storage, and a database record will be created.
    Preprocessing will be triggered asynchronously.
    """
    try:
        # Validate file
        file_content = await file.read()
        file_io = io.BytesIO(file_content)
        
        try:
            validate_image_file(file_io)
        except ImageValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        
        # Parse metadata if provided
        metadata_dict = None
        if metadata:
            import json
            try:
                metadata_dict = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON metadata",
                )
        
        # Upload to storage
        file_io.seek(0)
        original_name, thumbnail_name = storage_service.upload_image_with_thumbnail(
            file_io,
            settings.S3_BUCKET_GARMENTS,
        )
        
        # Generate URLs (handles both S3/MinIO and local storage)
        original_url = storage_service.get_file_url(settings.S3_BUCKET_GARMENTS, original_name)
        thumbnail_url = storage_service.get_file_url(settings.S3_BUCKET_GARMENTS, thumbnail_name)
        
        # Create database record
        garment = database.create_garment(
            db=db,
            original_image_url=original_url,
            thumbnail_url=thumbnail_url,
            name=name,
            metadata=metadata_dict,
        )
        
        logger.info("Garment uploaded", garment_id=str(garment.id), name=name)
        
        # Trigger async preprocessing task (if Celery available)
        try:
            from app.workers.tasks import preprocess_garment_task
            preprocess_garment_task.delay(str(garment.id))
        except ImportError:
            logger.warning("Celery not available - preprocessing will not run automatically")
            # In Colab, you can call preprocessing directly if needed
        
        return UploadResponse(
            id=garment.id,
            name=garment.name,
            image_url=garment.original_image_url,
            thumbnail_url=garment.thumbnail_url,
            status=garment.status,
            created_at=garment.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload garment", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload garment: {str(e)}",
        )


@router.get("", response_model=GarmentListResponse)
async def list_garments(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all garments with pagination."""
    try:
        garments, total = database.list_garments(
            db=db,
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        
        return GarmentListResponse(
            garments=[GarmentResponse.model_validate(garment) for garment in garments],
            total=total,
        )
    except Exception as e:
        logger.error("Failed to list garments", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list garments: {str(e)}",
        )


@router.get("/{garment_id}", response_model=GarmentResponse)
async def get_garment(
    garment_id: UUID,
    db: Session = Depends(get_db),
):
    """Get garment details by ID."""
    try:
        garment = database.get_garment_or_404(db, garment_id)
        return GarmentResponse.model_validate(garment)
    except GarmentNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get garment", garment_id=str(garment_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get garment: {str(e)}",
        )


@router.delete("/{garment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_garment(
    garment_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a garment and its associated data."""
    try:
        garment = database.get_garment_or_404(db, garment_id)
        
        # Delete from storage
        try:
            # Extract object name from URL
            original_url = garment.original_image_url
            object_name = original_url.split("/")[-1]
            storage_service.delete_file(settings.S3_BUCKET_GARMENTS, object_name)
            
            # Delete thumbnail
            if garment.thumbnail_url:
                thumbnail_name = garment.thumbnail_url.split("/")[-1]
                storage_service.delete_file(settings.S3_BUCKET_GARMENTS, thumbnail_name)
        except Exception as e:
            logger.warning("Failed to delete files from storage", error=str(e))
        
        # Delete from database
        database.delete_garment(db, garment_id)
        
        # Clear cache
        cache_service.delete(f"garment:{garment_id}")
        
        logger.info("Garment deleted", garment_id=str(garment_id))
        return None
        
    except GarmentNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to delete garment", garment_id=str(garment_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete garment: {str(e)}",
        )
