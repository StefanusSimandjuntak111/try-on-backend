"""Global exception handlers."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import TryOnException
from app.core.logging import get_logger

logger = get_logger(__name__)


async def tryon_exception_handler(request: Request, exc: TryOnException) -> JSONResponse:
    """Handle custom TryOn exceptions."""
    logger.warning(
        "TryOn exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.detail,
            "path": request.url.path,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "detail": exc.errors(),
            "path": request.url.path,
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    logger.error(
        "Database error",
        error=str(exc),
        path=request.url.path,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DatabaseError",
            "detail": "A database error occurred. Please try again later.",
            "path": request.url.path,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=exc.__class__.__name__,
        path=request.url.path,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "detail": "An unexpected error occurred. Please try again later.",
            "path": request.url.path,
        },
    )

