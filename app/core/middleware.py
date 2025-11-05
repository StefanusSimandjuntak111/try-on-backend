"""FastAPI middleware for logging and monitoring."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.monitoring import record_request_metrics

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        start_time = time.time()
        
        # Log request
        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
            query_params=dict(request.query_params) if request.query_params else None,
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=round(process_time, 4),
            )
            
            # Record metrics
            record_request_metrics(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time,
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=round(process_time, 4),
                exc_info=True,
            )
            
            # Record error metrics
            record_request_metrics(
                method=request.method,
                path=request.url.path,
                status_code=500,
                process_time=process_time,
            )
            
            raise

