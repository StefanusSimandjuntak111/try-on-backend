"""Image validation utilities."""

import io
from typing import BinaryIO, Tuple

from PIL import Image

from app.config import settings
from app.core.exceptions import ImageValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def validate_image_file(file: BinaryIO) -> Tuple[Image.Image, str]:
    """Validate and load an image file.

    Args:
        file: File-like object containing image data

    Returns:
        Tuple of (PIL Image, format string)

    Raises:
        ImageValidationError: If validation fails
    """
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to start

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise ImageValidationError(
            f"File size {file_size} exceeds maximum allowed size {settings.MAX_UPLOAD_SIZE}"
        )

    if file_size == 0:
        raise ImageValidationError("File is empty")

    # Read and validate image
    try:
        image_data = file.read()
        file.seek(0)
        
        # Validate format
        allowed_extensions = settings.ALLOWED_EXTENSIONS.lower().split(",")
        image = Image.open(io.BytesIO(image_data))
        
        # Check if format is supported
        format_lower = image.format.lower() if image.format else ""
        if format_lower not in [ext.strip() for ext in allowed_extensions]:
            raise ImageValidationError(
                f"Image format '{image.format}' not allowed. Allowed formats: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Validate image dimensions
        width, height = image.size
        max_dimension = settings.MAX_IMAGE_SIZE
        
        if width > max_dimension or height > max_dimension:
            raise ImageValidationError(
                f"Image dimensions {width}x{height} exceed maximum {max_dimension}x{max_dimension}"
            )
        
        if width < 64 or height < 64:
            raise ImageValidationError(
                f"Image dimensions {width}x{height} are too small. Minimum: 64x64"
            )
        
        # Verify image can be loaded and is valid
        image.verify()
        
        # Reopen image after verify (verify closes the image)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode not in ("RGB", "RGBA", "L"):
            image = image.convert("RGB")
        
        logger.debug(
            "Image validated",
            format=image.format,
            size=f"{width}x{height}",
            mode=image.mode,
        )
        
        return image, image.format or "JPEG"
        
    except Image.UnknownFormat as e:
        raise ImageValidationError(f"Unknown image format: {str(e)}")
    except Exception as e:
        raise ImageValidationError(f"Failed to validate image: {str(e)}")


def resize_image(
    image: Image.Image, max_size: int = None, target_size: Tuple[int, int] = None
) -> Image.Image:
    """Resize an image while maintaining aspect ratio.

    Args:
        image: PIL Image object
        max_size: Maximum dimension (maintains aspect ratio)
        target_size: Target size as (width, height) tuple

    Returns:
        Resized PIL Image
    """
    if max_size is None:
        max_size = settings.MAX_IMAGE_SIZE
    
    if target_size:
        return image.resize(target_size, Image.Resampling.LANCZOS)
    
    width, height = image.size
    
    if width <= max_size and height <= max_size:
        return image
    
    # Calculate new dimensions maintaining aspect ratio
    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))
    
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def normalize_image(image: Image.Image) -> Image.Image:
    """Normalize image format and mode.

    Args:
        image: PIL Image object

    Returns:
        Normalized PIL Image (RGB mode)
    """
    # Convert to RGB if necessary
    if image.mode == "RGBA":
        # Create white background
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        return background
    elif image.mode != "RGB":
        return image.convert("RGB")
    
    return image

