"""Celery tasks for async processing."""

import io
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from celery import Task
from PIL import Image
from sqlalchemy.orm import Session

from app.core.exceptions import ProcessingError
from app.core.logging import get_logger
from app.dependencies import SessionLocal
from app.config import settings
from app.services import database, inference_service, preprocessing_service, storage_service
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Celery task with database session management."""

    _db: Optional[Session] = None

    @property
    def db(self) -> Session:
        """Get database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completes."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(name="app.workers.tasks.preprocess_model_task", base=DatabaseTask, bind=True)
def preprocess_model_task(self, model_id: str):
    """Preprocess model image: background removal, parsing, pose estimation.

    Args:
        model_id: UUID of the model to preprocess
    """
    logger.info("Starting model preprocessing", model_id=model_id, task_id=self.request.id)
    
    try:
        db = self.db
        model = database.get_model_or_404(db, UUID(model_id))
        
        # Update status to processing
        database.update_model(db, UUID(model_id), status="processing")
        
        # Download image from storage
        object_name = model.original_image_url.split("/")[-1]
        image_data = storage_service.download_file(
            settings.S3_BUCKET_MODELS,
            object_name,
        )
        
        # Load image
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        # Preprocess using inference service
        preprocessing_result = inference_service.preprocess_model(image)
        
        # Store preprocessing results
        preprocessed_data = {
            "parsing": {
                "labels": preprocessing_result.get("parsing", {}).get("labels", []),
                "parsing_map": preprocessing_result.get("parsing", {}).get("parsing_map", {}).tolist() if preprocessing_result.get("parsing") else None,
            } if preprocessing_result.get("parsing") else None,
            "pose": preprocessing_result.get("pose"),
            "background_removed": preprocessing_result.get("metadata", {}).get("background_removed", False),
            "parsing_complete": preprocessing_result.get("metadata", {}).get("parsing_complete", False),
            "pose_estimated": preprocessing_result.get("metadata", {}).get("pose_estimated", False),
        }
        
        # Update model with preprocessing data and mark as ready
        database.update_model(
            db,
            UUID(model_id),
            status="ready",
            preprocessed_data=preprocessed_data,
        )
        
        logger.info("Model preprocessing completed", model_id=model_id, task_id=self.request.id)
        return {"status": "success", "model_id": model_id}
        
    except Exception as e:
        logger.error("Model preprocessing failed", model_id=model_id, error=str(e), task_id=self.request.id)
        
        # Update status to failed
        try:
            db = self.db
            database.update_model(
                db,
                UUID(model_id),
                status="failed",
            )
        except Exception:
            pass
        
        raise ProcessingError(f"Failed to preprocess model: {str(e)}")


@celery_app.task(name="app.workers.tasks.preprocess_garment_task", base=DatabaseTask, bind=True)
def preprocess_garment_task(self, garment_id: str):
    """Preprocess garment image: background removal, segmentation.

    Args:
        garment_id: UUID of the garment to preprocess
    """
    logger.info("Starting garment preprocessing", garment_id=garment_id, task_id=self.request.id)
    
    try:
        db = self.db
        garment = database.get_garment_or_404(db, UUID(garment_id))
        
        # Update status to processing
        database.update_garment(db, UUID(garment_id), status="processing")
        
        # Download image from storage
        object_name = garment.original_image_url.split("/")[-1]
        image_data = storage_service.download_file(
            settings.S3_BUCKET_GARMENTS,
            object_name,
        )
        
        # Load image
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        # Preprocess using inference service
        preprocessing_result = inference_service.preprocess_garment(image)
        
        # Store preprocessing results
        preprocessed_data = {
            "background_removed": preprocessing_result.get("metadata", {}).get("background_removed", False),
            "mask_generated": preprocessing_result.get("metadata", {}).get("mask_generated", False),
        }
        
        # Update garment with preprocessing data and mark as ready
        database.update_garment(
            db,
            UUID(garment_id),
            status="ready",
            preprocessed_data=preprocessed_data,
        )
        
        logger.info("Garment preprocessing completed", garment_id=garment_id, task_id=self.request.id)
        return {"status": "success", "garment_id": garment_id}
        
    except Exception as e:
        logger.error("Garment preprocessing failed", garment_id=garment_id, error=str(e), task_id=self.request.id)
        
        # Update status to failed
        try:
            db = self.db
            database.update_garment(
                db,
                UUID(garment_id),
                status="failed",
            )
        except Exception:
            pass
        
        raise ProcessingError(f"Failed to preprocess garment: {str(e)}")


@celery_app.task(name="app.workers.tasks.tryon_inference_task", base=DatabaseTask, bind=True)
def tryon_inference_task(self, job_id: str):
    """Perform try-on inference.

    Args:
        job_id: UUID of the try-on job
    """
    import time
    start_time = time.time()
    
    logger.info("Starting try-on inference", job_id=job_id, task_id=self.request.id)
    
    try:
        db = self.db
        job = database.get_job_or_404(db, UUID(job_id))
        
        # Update status to processing
        database.update_job(db, UUID(job_id), status="processing")
        
        # Get model and garment
        model = database.get_model_or_404(db, job.model_id)
        garment = database.get_garment_or_404(db, job.garment_id)
        
        # Check if model and garment are ready
        if model.status != "ready":
            raise ProcessingError(f"Model {job.model_id} is not ready (status: {model.status})")
        if garment.status != "ready":
            raise ProcessingError(f"Garment {job.garment_id} is not ready (status: {garment.status})")
        
        # Download images from storage
        model_object_name = model.original_image_url.split("/")[-1]
        model_data = storage_service.download_file(
            settings.S3_BUCKET_MODELS,
            model_object_name,
        )
        model_image = Image.open(io.BytesIO(model_data)).convert("RGB")
        
        garment_object_name = garment.original_image_url.split("/")[-1]
        garment_data = storage_service.download_file(
            settings.S3_BUCKET_GARMENTS,
            garment_object_name,
        )
        garment_image = Image.open(io.BytesIO(garment_data)).convert("RGB")
        
        # Use preprocessed data if available
        model_preprocessing = None
        garment_preprocessing = None
        
        if model.preprocessed_data:
            # Reconstruct preprocessing results from stored data
            # This is simplified - in practice, you might want to store actual masks/parsing
            model_preprocessing = {
                "parsing": model.preprocessed_data.get("parsing"),
                "pose": model.preprocessed_data.get("pose"),
            }
        
        if garment.preprocessed_data:
            garment_preprocessing = {
                "mask": None,  # Would need to reconstruct from stored data
            }
        
        # Perform try-on inference
        result_image = inference_service.perform_tryon(
            model_image=model_image,
            garment_image=garment_image,
            model_preprocessing=model_preprocessing,
            garment_preprocessing=garment_preprocessing,
        )
        
        # Upload result to storage
        result_bytes = preprocessing_service.image_to_bytes(result_image)
        result_io = io.BytesIO(result_bytes)
        result_object_name = f"{job_id}.jpg"
        
        storage_service.upload_file(
            result_io,
            settings.S3_BUCKET_RESULTS,
            result_object_name,
            content_type="image/jpeg",
        )
        
        # Generate result URL
        result_url = f"{settings.S3_ENDPOINT}/{settings.S3_BUCKET_RESULTS}/{result_object_name}"
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Update job with result
        database.update_job(
            db,
            UUID(job_id),
            status="completed",
            result_url=result_url,
            processing_time=processing_time,
            completed_at=datetime.utcnow(),
        )
        
        logger.info(
            "Try-on inference completed",
            job_id=job_id,
            processing_time=processing_time,
            task_id=self.request.id,
        )
        
        return {
            "status": "success",
            "job_id": job_id,
            "result_url": result_url,
            "processing_time": processing_time,
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            "Try-on inference failed",
            job_id=job_id,
            error=str(e),
            processing_time=processing_time,
            task_id=self.request.id,
        )
        
        # Update status to failed
        try:
            db = self.db
            database.update_job(
                db,
                UUID(job_id),
                status="failed",
                error_message=str(e),
                processing_time=processing_time,
            )
        except Exception:
            pass
        
        raise ProcessingError(f"Failed to perform try-on: {str(e)}")


@celery_app.task(name="app.workers.tasks.cleanup_old_files_task", base=DatabaseTask, bind=True)
def cleanup_old_files_task(self, days_old: int = 30):
    """Clean up old files and records.

    Args:
        days_old: Delete files older than this many days (default: 30)
    """
    logger.info("Starting cleanup task", days_old=days_old, task_id=self.request.id)
    
    try:
        db = self.db
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        # Find old completed jobs
        old_jobs, _ = database.list_jobs(
            db,
            skip=0,
            limit=1000,
            status="completed",
        )
        
        deleted_count = 0
        for job in old_jobs:
            if job.completed_at and job.completed_at < cutoff_date:
                try:
                    # Delete result file
                    if job.result_url:
                        object_name = job.result_url.split("/")[-1]
                        storage_service.delete_file(
                            settings.S3_BUCKET_RESULTS,
                            object_name,
                        )
                    
                    # Delete job record
                    database.delete_job(db, job.id)
                    deleted_count += 1
                except Exception as e:
                    logger.warning("Failed to delete old job", job_id=str(job.id), error=str(e))
        
        logger.info("Cleanup task completed", deleted_count=deleted_count, task_id=self.request.id)
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error("Cleanup task failed", error=str(e), task_id=self.request.id)
        raise ProcessingError(f"Failed to cleanup old files: {str(e)}")


# Periodic task configuration (can be set up via celerybeat)
try:
    from celery.schedules import crontab
    
    @celery_app.on_after_configure.connect
    def setup_periodic_tasks(sender, **kwargs):
        """Setup periodic tasks."""
        # Run cleanup daily at 2 AM
        sender.add_periodic_task(
            crontab(hour=2, minute=0),
            cleanup_old_files_task.s(days_old=30),
            name="daily-cleanup",
        )
except ImportError:
    logger.warning("celery.schedules not available, periodic tasks disabled")

