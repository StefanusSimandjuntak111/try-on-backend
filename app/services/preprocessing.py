"""Image preprocessing service."""

import io
from typing import BinaryIO, Optional

import numpy as np
from PIL import Image

from app.config import settings
from app.core.logging import get_logger
from app.services.validation import normalize_image, resize_image, validate_image_file

logger = get_logger(__name__)


class PreprocessingService:
    """Image preprocessing service."""

    def __init__(self):
        """Initialize preprocessing service."""
        self.target_size = (768, 1024)  # Standard try-on dimensions
        logger.info("Preprocessing service initialized")

    def preprocess_model_image(
        self, file: BinaryIO, normalize: bool = True
    ) -> tuple[Image.Image, dict]:
        """Preprocess a model image for try-on.

        Args:
            file: File-like object containing image data
            normalize: Whether to normalize the image

        Returns:
            Tuple of (preprocessed PIL Image, metadata dict)
        """
        # Validate image
        image, format_str = validate_image_file(file)
        
        metadata = {
            "original_format": format_str,
            "original_size": image.size,
            "original_mode": image.mode,
        }
        
        # Resize to target dimensions
        if image.size != self.target_size:
            image = resize_image(image, target_size=self.target_size)
            metadata["resized"] = True
            metadata["resized_size"] = image.size
        else:
            metadata["resized"] = False
        
        # Normalize image
        if normalize:
            image = normalize_image(image)
            metadata["normalized"] = True
            metadata["normalized_mode"] = image.mode
        else:
            metadata["normalized"] = False
        
        logger.debug(
            "Model image preprocessed",
            original_size=metadata["original_size"],
            final_size=image.size,
        )
        
        return image, metadata

    def preprocess_garment_image(
        self, file: BinaryIO, normalize: bool = True
    ) -> tuple[Image.Image, dict]:
        """Preprocess a garment image for try-on.

        Args:
            file: File-like object containing image data
            normalize: Whether to normalize the image

        Returns:
            Tuple of (preprocessed PIL Image, metadata dict)
        """
        # Validate image
        image, format_str = validate_image_file(file)
        
        metadata = {
            "original_format": format_str,
            "original_size": image.size,
            "original_mode": image.mode,
        }
        
        # For garments, we might want to preserve aspect ratio
        # but ensure it fits within reasonable bounds
        max_dimension = max(self.target_size)
        if max(image.size) > max_dimension:
            image = resize_image(image, max_size=max_dimension)
            metadata["resized"] = True
            metadata["resized_size"] = image.size
        else:
            metadata["resized"] = False
        
        # Normalize image
        if normalize:
            image = normalize_image(image)
            metadata["normalized"] = True
            metadata["normalized_mode"] = image.mode
        else:
            metadata["normalized"] = False
        
        logger.debug(
            "Garment image preprocessed",
            original_size=metadata["original_size"],
            final_size=image.size,
        )
        
        return image, metadata

    def image_to_bytes(self, image: Image.Image, format: str = "JPEG") -> bytes:
        """Convert PIL Image to bytes.

        Args:
            image: PIL Image object
            format: Image format (JPEG, PNG, etc.)

        Returns:
            Image bytes
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format, quality=95)
        buffer.seek(0)
        return buffer.getvalue()

    def image_to_numpy(self, image: Image.Image) -> np.ndarray:
        """Convert PIL Image to numpy array.

        Args:
            image: PIL Image object

        Returns:
            Numpy array (H, W, C)
        """
        return np.array(image)

    def numpy_to_image(self, array: np.ndarray) -> Image.Image:
        """Convert numpy array to PIL Image.

        Args:
            array: Numpy array (H, W, C) or (H, W)

        Returns:
            PIL Image object
        """
        # Ensure array is in correct format
        if array.dtype != np.uint8:
            # Normalize to 0-255 range
            if array.max() <= 1.0:
                array = (array * 255).astype(np.uint8)
            else:
                array = array.astype(np.uint8)
        
        if len(array.shape) == 2:
            # Grayscale
            return Image.fromarray(array, mode="L")
        elif len(array.shape) == 3:
            if array.shape[2] == 3:
                # RGB
                return Image.fromarray(array, mode="RGB")
            elif array.shape[2] == 4:
                # RGBA
                return Image.fromarray(array, mode="RGBA")
            else:
                raise ValueError(f"Unsupported array shape: {array.shape}")
        else:
            raise ValueError(f"Unsupported array shape: {array.shape}")


# Global preprocessing service instance
preprocessing_service = PreprocessingService()

