"""Model management endpoints."""

import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.exceptions import ImageValidationError, ModelNotFoundError
from app.core.logging import get_logger
from app.dependencies import get_db
from app.models.schemas import ModelListResponse, ModelResponse, UploadResponse
from app.services import database
from app.services.cache import cache_service
from app.services.storage import storage_service
from app.services.validation import validate_image_file

router = APIRouter()
logger = get_logger(__name__)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_model(
    file: UploadFile = File(..., description="Model image file"),
    name: Optional[str] = Form(None, description="Model name"),
    metadata: Optional[str] = Form(None, description="JSON metadata"),
    db: Session = Depends(get_db),
):
    """Upload human model image.

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
            settings.S3_BUCKET_MODELS,
        )
        
        # Generate URLs (handles both S3/MinIO and local storage)
        original_url = storage_service.get_file_url(settings.S3_BUCKET_MODELS, original_name)
        thumbnail_url = storage_service.get_file_url(settings.S3_BUCKET_MODELS, thumbnail_name)
        
        # Create database record
        model = database.create_model(
            db=db,
            original_image_url=original_url,
            thumbnail_url=thumbnail_url,
            name=name,
            metadata=metadata_dict,
        )
        
        logger.info("Model uploaded", model_id=str(model.id), name=name)
        
        # Trigger async preprocessing task (if Celery available)
        try:
            from app.workers.tasks import preprocess_model_task
            preprocess_model_task.delay(str(model.id))
        except ImportError:
            logger.warning("Celery not available - preprocessing will not run automatically")
            # In Colab, you can call preprocessing directly if needed
        
        return UploadResponse(
            id=model.id,
            name=model.name,
            image_url=model.original_image_url,
            thumbnail_url=model.thumbnail_url,
            status=model.status,
            created_at=model.created_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload model", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload model: {str(e)}",
        )


@router.get("", response_model=ModelListResponse)
async def list_models(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all models with pagination."""
    try:
        models, total = database.list_models(
            db=db,
            skip=skip,
            limit=limit,
            status=status_filter,
        )
        
        return ModelListResponse(
            models=[ModelResponse.model_validate(model) for model in models],
            total=total,
        )
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}",
        )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: UUID,
    db: Session = Depends(get_db),
):
    """Get model details by ID."""
    try:
        model = database.get_model_or_404(db, model_id)
        return ModelResponse.model_validate(model)
    except ModelNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to get model", model_id=str(model_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model: {str(e)}",
        )


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    model_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a model and its associated data."""
    try:
        model = database.get_model_or_404(db, model_id)
        
        # Delete from storage
        try:
            # Extract object name from URL
            original_url = model.original_image_url
            object_name = original_url.split("/")[-1]
            storage_service.delete_file(settings.S3_BUCKET_MODELS, object_name)
            
            # Delete thumbnail
            if model.thumbnail_url:
                thumbnail_name = model.thumbnail_url.split("/")[-1]
                storage_service.delete_file(settings.S3_BUCKET_MODELS, thumbnail_name)
        except Exception as e:
            logger.warning("Failed to delete files from storage", error=str(e))
        
        # Delete from database
        database.delete_model(db, model_id)
        
        # Clear cache
        cache_service.delete(f"model:{model_id}")
        
        logger.info("Model deleted", model_id=str(model_id))
        return None
        
    except ModelNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to delete model", model_id=str(model_id), error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete model: {str(e)}",
        )
