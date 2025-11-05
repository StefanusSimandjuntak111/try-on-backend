"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Try-On Backend"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/tryon_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Storage (S3/MinIO)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_MODELS: str = "models"
    S3_BUCKET_GARMENTS: str = "garments"
    S3_BUCKET_RESULTS: str = "results"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # ML Models
    ML_DEVICE: str = "cuda"  # or "cpu"
    HRVITON_CHECKPOINT: str = "./weights/hrviton.pth"
    SCHP_CHECKPOINT: str = "./weights/schp.pth"
    OPENPOSE_CHECKPOINT: str = "./weights/openpose.pth"
    U2NET_CHECKPOINT: str = "./weights/u2net.pth"

    # Processing
    MAX_IMAGE_SIZE: int = 2048
    THUMBNAIL_SIZE: int = 256
    CACHE_TTL: int = 3600  # 1 hour

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Security
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

