"""Monitoring and metrics utilities."""

from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Job metrics
tryon_jobs_total = Counter(
    "tryon_jobs_total",
    "Total number of try-on jobs",
    ["status"],
)

tryon_job_duration_seconds = Histogram(
    "tryon_job_duration_seconds",
    "Try-on job processing duration in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

# Task metrics
celery_tasks_total = Counter(
    "celery_tasks_total",
    "Total number of Celery tasks",
    ["task_name", "status"],
)

celery_task_duration_seconds = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# Storage metrics
storage_operations_total = Counter(
    "storage_operations_total",
    "Total number of storage operations",
    ["operation", "bucket"],
)

storage_operation_duration_seconds = Histogram(
    "storage_operation_duration_seconds",
    "Storage operation duration in seconds",
    ["operation"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0),
)

# Model metrics
ml_model_inference_total = Counter(
    "ml_model_inference_total",
    "Total number of ML model inferences",
    ["model_name", "status"],
)

ml_model_inference_duration_seconds = Histogram(
    "ml_model_inference_duration_seconds",
    "ML model inference duration in seconds",
    ["model_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

# Active jobs gauge
active_jobs = Gauge(
    "active_jobs",
    "Number of active try-on jobs",
    ["status"],
)

# Database connection pool
db_pool_size = Gauge(
    "db_pool_size",
    "Database connection pool size",
    ["state"],  # "active", "idle", "overflow"
)


def record_request_metrics(
    method: str,
    path: str,
    status_code: int,
    process_time: float,
) -> None:
    """Record HTTP request metrics."""
    # Normalize path (remove IDs)
    normalized_path = _normalize_path(path)
    
    http_requests_total.labels(
        method=method,
        path=normalized_path,
        status_code=status_code,
    ).inc()
    
    http_request_duration_seconds.labels(
        method=method,
        path=normalized_path,
    ).observe(process_time)


def record_job_metrics(status: str, duration: float = None) -> None:
    """Record try-on job metrics."""
    tryon_jobs_total.labels(status=status).inc()
    if duration is not None:
        tryon_job_duration_seconds.observe(duration)


def record_task_metrics(task_name: str, status: str, duration: float = None) -> None:
    """Record Celery task metrics."""
    celery_tasks_total.labels(task_name=task_name, status=status).inc()
    if duration is not None:
        celery_task_duration_seconds.labels(task_name=task_name).observe(duration)


def record_storage_metrics(operation: str, bucket: str, duration: float = None) -> None:
    """Record storage operation metrics."""
    storage_operations_total.labels(operation=operation, bucket=bucket).inc()
    if duration is not None:
        storage_operation_duration_seconds.labels(operation=operation).observe(duration)


def record_ml_inference_metrics(model_name: str, status: str, duration: float = None) -> None:
    """Record ML model inference metrics."""
    ml_model_inference_total.labels(model_name=model_name, status=status).inc()
    if duration is not None:
        ml_model_inference_duration_seconds.labels(model_name=model_name).observe(duration)


def update_active_jobs(status: str, count: int) -> None:
    """Update active jobs gauge."""
    active_jobs.labels(status=status).set(count)


def _normalize_path(path: str) -> str:
    """Normalize path by replacing UUIDs and IDs with placeholders."""
    import re
    # Replace UUIDs
    path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', path)
    # Replace numeric IDs
    path = re.sub(r'/\d+', '/{id}', path)
    return path

