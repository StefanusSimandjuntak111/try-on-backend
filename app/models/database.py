"""SQLAlchemy database models."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, Float, ForeignKey, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Model(Base):
    """Human model database model."""

    __tablename__ = "models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)
    original_image_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    preprocessed_data = Column(JSON, nullable=True)  # Store parsing, pose data
    extra_metadata = Column("metadata", JSON, nullable=True)  # Additional metadata (mapped to 'metadata' column)
    status = Column(
        String(50), nullable=False, default="processing"
    )  # 'processing', 'ready', 'failed'
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    tryon_jobs = relationship("TryOnJob", back_populates="model", cascade="all, delete-orphan")

    @property
    def metadata(self) -> Any:
        """Property to access extra_metadata as metadata for API compatibility."""
        return self.extra_metadata

    @metadata.setter
    def metadata(self, value: Any) -> None:
        """Property setter for metadata."""
        self.extra_metadata = value

    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name={self.name}, status={self.status})>"


class Garment(Base):
    """Garment database model."""

    __tablename__ = "garments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)
    original_image_url = Column(Text, nullable=False)
    thumbnail_url = Column(Text, nullable=True)
    preprocessed_data = Column(JSON, nullable=True)  # Store segmentation data
    extra_metadata = Column("metadata", JSON, nullable=True)  # size, color, category (mapped to 'metadata' column)
    status = Column(
        String(50), nullable=False, default="processing"
    )  # 'processing', 'ready', 'failed'
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    tryon_jobs = relationship(
        "TryOnJob", back_populates="garment", cascade="all, delete-orphan"
    )

    @property
    def metadata(self) -> Any:
        """Property to access extra_metadata as metadata for API compatibility."""
        return self.extra_metadata

    @metadata.setter
    def metadata(self, value: Any) -> None:
        """Property setter for metadata."""
        self.extra_metadata = value

    def __repr__(self) -> str:
        return f"<Garment(id={self.id}, name={self.name}, status={self.status})>"


class TryOnJob(Base):
    """Try-on job database model."""

    __tablename__ = "tryon_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False)
    garment_id = Column(UUID(as_uuid=True), ForeignKey("garments.id"), nullable=False)
    result_url = Column(Text, nullable=True)
    status = Column(
        String(50), nullable=False, default="queued"
    )  # 'queued', 'processing', 'completed', 'failed'
    error_message = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)
    options = Column(JSON, nullable=True)  # Processing options
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    model = relationship("Model", back_populates="tryon_jobs")
    garment = relationship("Garment", back_populates="tryon_jobs")

    def __repr__(self) -> str:
        return f"<TryOnJob(id={self.id}, status={self.status}, model_id={self.model_id}, garment_id={self.garment_id})>"

