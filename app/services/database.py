"""Database CRUD operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import GarmentNotFoundError, JobNotFoundError, ModelNotFoundError
from app.models.database import Garment, Model, TryOnJob

# Model CRUD operations


def get_model(db: Session, model_id: UUID) -> Optional[Model]:
    """Get a model by ID."""
    return db.query(Model).filter(Model.id == model_id).first()


def get_model_or_404(db: Session, model_id: UUID) -> Model:
    """Get a model by ID or raise 404."""
    model = get_model(db, model_id)
    if not model:
        raise ModelNotFoundError(str(model_id))
    return model


def list_models(
    db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None
) -> tuple[List[Model], int]:
    """List models with pagination."""
    query = db.query(Model)
    
    if status:
        query = query.filter(Model.status == status)
    
    total = query.count()
    models = query.offset(skip).limit(limit).all()
    
    return models, total


def create_model(
    db: Session,
    original_image_url: str,
    thumbnail_url: Optional[str] = None,
    name: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Model:
    """Create a new model."""
    model = Model(
        original_image_url=original_image_url,
        thumbnail_url=thumbnail_url,
        name=name,
        metadata=metadata,
        status="processing",
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_model(
    db: Session,
    model_id: UUID,
    name: Optional[str] = None,
    status: Optional[str] = None,
    preprocessed_data: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> Model:
    """Update a model."""
    model = get_model_or_404(db, model_id)
    
    if name is not None:
        model.name = name
    if status is not None:
        model.status = status
    if preprocessed_data is not None:
        model.preprocessed_data = preprocessed_data
    if metadata is not None:
        model.metadata = metadata
    
    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model_id: UUID) -> None:
    """Delete a model."""
    model = get_model_or_404(db, model_id)
    db.delete(model)
    db.commit()


# Garment CRUD operations


def get_garment(db: Session, garment_id: UUID) -> Optional[Garment]:
    """Get a garment by ID."""
    return db.query(Garment).filter(Garment.id == garment_id).first()


def get_garment_or_404(db: Session, garment_id: UUID) -> Garment:
    """Get a garment by ID or raise 404."""
    garment = get_garment(db, garment_id)
    if not garment:
        raise GarmentNotFoundError(str(garment_id))
    return garment


def list_garments(
    db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None
) -> tuple[List[Garment], int]:
    """List garments with pagination."""
    query = db.query(Garment)
    
    if status:
        query = query.filter(Garment.status == status)
    
    total = query.count()
    garments = query.offset(skip).limit(limit).all()
    
    return garments, total


def create_garment(
    db: Session,
    original_image_url: str,
    thumbnail_url: Optional[str] = None,
    name: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Garment:
    """Create a new garment."""
    garment = Garment(
        original_image_url=original_image_url,
        thumbnail_url=thumbnail_url,
        name=name,
        metadata=metadata,
        status="processing",
    )
    db.add(garment)
    db.commit()
    db.refresh(garment)
    return garment


def update_garment(
    db: Session,
    garment_id: UUID,
    name: Optional[str] = None,
    status: Optional[str] = None,
    preprocessed_data: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> Garment:
    """Update a garment."""
    garment = get_garment_or_404(db, garment_id)
    
    if name is not None:
        garment.name = name
    if status is not None:
        garment.status = status
    if preprocessed_data is not None:
        garment.preprocessed_data = preprocessed_data
    if metadata is not None:
        garment.metadata = metadata
    
    db.commit()
    db.refresh(garment)
    return garment


def delete_garment(db: Session, garment_id: UUID) -> None:
    """Delete a garment."""
    garment = get_garment_or_404(db, garment_id)
    db.delete(garment)
    db.commit()


# Try-on Job CRUD operations


def get_job(db: Session, job_id: UUID) -> Optional[TryOnJob]:
    """Get a job by ID."""
    return db.query(TryOnJob).filter(TryOnJob.id == job_id).first()


def get_job_or_404(db: Session, job_id: UUID) -> TryOnJob:
    """Get a job by ID or raise 404."""
    job = get_job(db, job_id)
    if not job:
        raise JobNotFoundError(str(job_id))
    return job


def list_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    model_id: Optional[UUID] = None,
    garment_id: Optional[UUID] = None,
) -> tuple[List[TryOnJob], int]:
    """List jobs with pagination and filters."""
    query = db.query(TryOnJob)
    
    if status:
        query = query.filter(TryOnJob.status == status)
    if model_id:
        query = query.filter(TryOnJob.model_id == model_id)
    if garment_id:
        query = query.filter(TryOnJob.garment_id == garment_id)
    
    total = query.count()
    jobs = query.order_by(TryOnJob.created_at.desc()).offset(skip).limit(limit).all()
    
    return jobs, total


def create_job(
    db: Session,
    model_id: UUID,
    garment_id: UUID,
    options: Optional[dict] = None,
) -> TryOnJob:
    """Create a new try-on job."""
    job = TryOnJob(
        model_id=model_id,
        garment_id=garment_id,
        options=options,
        status="queued",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job(
    db: Session,
    job_id: UUID,
    status: Optional[str] = None,
    result_url: Optional[str] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None,
) -> TryOnJob:
    """Update a job."""
    job = get_job_or_404(db, job_id)
    
    if status is not None:
        job.status = status
    if result_url is not None:
        job.result_url = result_url
    if error_message is not None:
        job.error_message = error_message
    if processing_time is not None:
        job.processing_time = processing_time
    
    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job_id: UUID) -> None:
    """Delete a job."""
    job = get_job_or_404(db, job_id)
    db.delete(job)
    db.commit()

