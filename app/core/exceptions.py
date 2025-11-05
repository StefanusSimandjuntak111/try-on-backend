"""Custom exceptions."""

from fastapi import HTTPException, status


class TryOnException(HTTPException):
    """Base exception for try-on operations."""

    pass


class ModelNotFoundError(TryOnException):
    """Model not found exception."""

    def __init__(self, model_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {model_id} not found",
        )


class GarmentNotFoundError(TryOnException):
    """Garment not found exception."""

    def __init__(self, garment_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garment with id {garment_id} not found",
        )


class JobNotFoundError(TryOnException):
    """Job not found exception."""

    def __init__(self, job_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found",
        )


class ImageValidationError(TryOnException):
    """Image validation error."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image validation failed: {message}",
        )


class ProcessingError(TryOnException):
    """Processing error."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {message}",
        )


class StorageError(TryOnException):
    """Storage error."""

    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage operation failed: {message}",
        )

