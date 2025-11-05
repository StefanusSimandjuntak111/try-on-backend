"""S3/MinIO storage service."""

import io
from typing import BinaryIO, Optional
from uuid import UUID, uuid4

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from minio import Minio
from minio.error import S3Error
from PIL import Image

from app.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """Storage service for S3-compatible storage."""

    def __init__(self):
        """Initialize storage service."""
        self.use_minio = settings.S3_ENDPOINT.startswith("http://localhost") or settings.S3_ENDPOINT.startswith("http://127.0.0.1")
        
        if self.use_minio:
            self._init_minio()
        else:
            self._init_boto3()
        
        self._ensure_buckets()

    def _init_minio(self) -> None:
        """Initialize MinIO client."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(settings.S3_ENDPOINT)
            self.minio_client = Minio(
                parsed.netloc or parsed.path.lstrip("/"),
                access_key=settings.S3_ACCESS_KEY,
                secret_key=settings.S3_SECRET_KEY,
                secure=settings.S3_USE_SSL,
            )
            logger.info("Initialized MinIO client", endpoint=settings.S3_ENDPOINT)
        except Exception as e:
            logger.error("Failed to initialize MinIO client", error=str(e))
            raise StorageError(f"Failed to initialize MinIO: {str(e)}")

    def _init_boto3(self) -> None:
        """Initialize boto3 S3 client."""
        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                use_ssl=settings.S3_USE_SSL,
                config=Config(signature_version="s3v4"),
            )
            logger.info("Initialized boto3 S3 client", endpoint=settings.S3_ENDPOINT)
        except Exception as e:
            logger.error("Failed to initialize boto3 client", error=str(e))
            raise StorageError(f"Failed to initialize S3: {str(e)}")

    def _ensure_buckets(self) -> None:
        """Ensure all required buckets exist."""
        buckets = [
            settings.S3_BUCKET_MODELS,
            settings.S3_BUCKET_GARMENTS,
            settings.S3_BUCKET_RESULTS,
        ]
        
        for bucket in buckets:
            try:
                if self.use_minio:
                    if not self.minio_client.bucket_exists(bucket):
                        self.minio_client.make_bucket(bucket)
                        logger.info("Created bucket", bucket=bucket)
                else:
                    self.s3_client.head_bucket(Bucket=bucket)
            except (S3Error, ClientError) as e:
                if self.use_minio:
                    if not self.minio_client.bucket_exists(bucket):
                        self.minio_client.make_bucket(bucket)
                        logger.info("Created bucket", bucket=bucket)
                else:
                    try:
                        self.s3_client.create_bucket(Bucket=bucket)
                        logger.info("Created bucket", bucket=bucket)
                    except Exception as create_error:
                        logger.warning("Bucket creation issue", bucket=bucket, error=str(create_error))

    def upload_file(
        self,
        file_data: BinaryIO,
        bucket: str,
        object_name: Optional[str] = None,
        content_type: str = "image/jpeg",
    ) -> str:
        """Upload a file to storage.

        Args:
            file_data: File-like object to upload
            bucket: Bucket name
            object_name: Object name (will generate UUID if not provided)
            content_type: Content type of the file

        Returns:
            Object name/path
        """
        if object_name is None:
            object_name = f"{uuid4()}.jpg"

        try:
            file_data.seek(0)
            
            if self.use_minio:
                # Get file size
                file_data.seek(0, 2)
                file_size = file_data.tell()
                file_data.seek(0)
                
                self.minio_client.put_object(
                    bucket,
                    object_name,
                    file_data,
                    length=file_size,
                    part_size=10 * 1024 * 1024,
                    content_type=content_type,
                )
            else:
                file_data.seek(0)
                self.s3_client.upload_fileobj(
                    file_data,
                    bucket,
                    object_name,
                    ExtraArgs={"ContentType": content_type},
                )
            
            logger.info("File uploaded", bucket=bucket, object_name=object_name)
            return object_name
        except (S3Error, ClientError) as e:
            logger.error("Failed to upload file", bucket=bucket, error=str(e))
            raise StorageError(f"Failed to upload file: {str(e)}")

    def download_file(self, bucket: str, object_name: str) -> bytes:
        """Download a file from storage.

        Args:
            bucket: Bucket name
            object_name: Object name

        Returns:
            File content as bytes
        """
        try:
            if self.use_minio:
                response = self.minio_client.get_object(bucket, object_name)
                data = response.read()
                response.close()
                response.release_conn()
            else:
                response = self.s3_client.get_object(Bucket=bucket, Key=object_name)
                data = response["Body"].read()
            
            logger.debug("File downloaded", bucket=bucket, object_name=object_name)
            return data
        except (S3Error, ClientError) as e:
            logger.error("Failed to download file", bucket=bucket, object_name=object_name, error=str(e))
            raise StorageError(f"Failed to download file: {str(e)}")

    def delete_file(self, bucket: str, object_name: str) -> None:
        """Delete a file from storage.

        Args:
            bucket: Bucket name
            object_name: Object name
        """
        try:
            if self.use_minio:
                self.minio_client.remove_object(bucket, object_name)
            else:
                self.s3_client.delete_object(Bucket=bucket, Key=object_name)
            
            logger.info("File deleted", bucket=bucket, object_name=object_name)
        except (S3Error, ClientError) as e:
            logger.error("Failed to delete file", bucket=bucket, object_name=object_name, error=str(e))
            raise StorageError(f"Failed to delete file: {str(e)}")

    def get_presigned_url(
        self, bucket: str, object_name: str, expiration: int = 3600
    ) -> str:
        """Generate a presigned URL for temporary access.

        Args:
            bucket: Bucket name
            object_name: Object name
            expiration: URL expiration time in seconds

        Returns:
            Presigned URL
        """
        try:
            if self.use_minio:
                from datetime import timedelta
                url = self.minio_client.presigned_get_object(
                    bucket, object_name, expires=timedelta(seconds=expiration)
                )
            else:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": object_name},
                    ExpiresIn=expiration,
                )
            
            return url
        except (S3Error, ClientError) as e:
            logger.error("Failed to generate presigned URL", bucket=bucket, object_name=object_name, error=str(e))
            raise StorageError(f"Failed to generate presigned URL: {str(e)}")

    def generate_thumbnail(
        self, image_data: bytes, size: int = None
    ) -> bytes:
        """Generate a thumbnail from image data.

        Args:
            image_data: Original image bytes
            size: Thumbnail size (default from settings)

        Returns:
            Thumbnail image bytes
        """
        if size is None:
            size = settings.THUMBNAIL_SIZE

        try:
            image = Image.open(io.BytesIO(image_data))
            image.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
                image = background
            
            thumbnail_io = io.BytesIO()
            image.save(thumbnail_io, format="JPEG", quality=85)
            thumbnail_io.seek(0)
            
            return thumbnail_io.getvalue()
        except Exception as e:
            logger.error("Failed to generate thumbnail", error=str(e))
            raise StorageError(f"Failed to generate thumbnail: {str(e)}")

    def upload_image_with_thumbnail(
        self,
        file_data: BinaryIO,
        bucket: str,
        object_name: Optional[str] = None,
    ) -> tuple[str, str]:
        """Upload an image and its thumbnail.

        Args:
            file_data: File-like object to upload
            bucket: Bucket name
            object_name: Object name (will generate UUID if not provided)

        Returns:
            Tuple of (original_object_name, thumbnail_object_name)
        """
        # Read image data
        file_data.seek(0)
        image_data = file_data.read()
        
        # Upload original
        file_data.seek(0)
        original_name = self.upload_file(
            file_data, bucket, object_name, content_type="image/jpeg"
        )
        
        # Generate and upload thumbnail
        thumbnail_data = self.generate_thumbnail(image_data)
        thumbnail_name = f"{original_name.rsplit('.', 1)[0]}_thumb.jpg"
        thumbnail_io = io.BytesIO(thumbnail_data)
        
        self.upload_file(
            thumbnail_io,
            bucket,
            thumbnail_name,
            content_type="image/jpeg",
        )
        
        return original_name, thumbnail_name


# Global storage service instance
storage_service = StorageService()

