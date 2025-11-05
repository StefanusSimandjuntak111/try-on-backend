"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True
        json_encoders = {UUID: str}


# Model schemas
class ModelMetadata(BaseModel):
    """Model metadata schema."""

    height: Optional[int] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    custom: Optional[dict[str, Any]] = None


class ModelCreate(BaseSchema):
    """Model creation schema."""

    name: Optional[str] = None
    metadata: Optional[ModelMetadata] = None


class ModelResponse(BaseSchema):
    """Model response schema."""

    id: UUID
    name: Optional[str]
    original_image_url: str
    thumbnail_url: Optional[str]
    preprocessed_data: Optional[dict[str, Any]]
    metadata: Optional[dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime


class ModelListResponse(BaseSchema):
    """Model list response schema."""

    models: list[ModelResponse]
    total: int


# Garment schemas
class GarmentMetadata(BaseModel):
    """Garment metadata schema."""

    size: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    custom: Optional[dict[str, Any]] = None


class GarmentCreate(BaseSchema):
    """Garment creation schema."""

    name: Optional[str] = None
    metadata: Optional[GarmentMetadata] = None


class GarmentResponse(BaseSchema):
    """Garment response schema."""

    id: UUID
    name: Optional[str]
    original_image_url: str
    thumbnail_url: Optional[str]
    preprocessed_data: Optional[dict[str, Any]]
    metadata: Optional[dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime


class GarmentListResponse(BaseSchema):
    """Garment list response schema."""

    garments: list[GarmentResponse]
    total: int


# Try-on job schemas
class TryOnOptions(BaseModel):
    """Try-on processing options."""

    size: Optional[str] = Field(None, description="Garment size")
    quality: Optional[str] = Field("high", description="Output quality: 'low', 'medium', 'high'")
    background: Optional[str] = Field(None, description="Background type: 'original', 'transparent', 'white'")
    custom: Optional[dict[str, Any]] = None


class TryOnCreate(BaseSchema):
    """Try-on job creation schema."""

    model_id: UUID = Field(..., description="Human model ID")
    garment_id: UUID = Field(..., description="Garment ID")
    options: Optional[TryOnOptions] = None


class TryOnResponse(BaseSchema):
    """Try-on job response schema."""

    id: UUID
    model_id: UUID
    garment_id: UUID
    result_url: Optional[str]
    status: str
    error_message: Optional[str]
    processing_time: Optional[float]
    options: Optional[dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]


class TryOnStatusResponse(BaseSchema):
    """Try-on job status response schema."""

    id: UUID
    status: str
    error_message: Optional[str]
    estimated_time: Optional[int] = Field(None, description="Estimated remaining time in seconds")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    created_at: datetime
    completed_at: Optional[datetime]


class TryOnListResponse(BaseSchema):
    """Try-on job list response schema."""

    jobs: list[TryOnResponse]
    total: int


# Upload response
class UploadResponse(BaseSchema):
    """File upload response schema."""

    id: UUID
    name: Optional[str]
    image_url: str
    thumbnail_url: Optional[str]
    status: str
    created_at: datetime


# Health check schemas
class HealthResponse(BaseSchema):
    """Health check response schema."""

    status: str
    timestamp: datetime


class ModelsHealthResponse(BaseSchema):
    """ML models health response schema."""

    status: str
    models: dict[str, dict[str, Any]]


