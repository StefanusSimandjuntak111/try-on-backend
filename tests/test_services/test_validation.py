"""Tests for validation service."""

import pytest
from PIL import Image
import io

from app.services.validation import validate_image_file, resize_image, normalize_image
from app.core.exceptions import ImageValidationError
from app.config import settings


def test_validate_image_file_valid(sample_image_file):
    """Test validating a valid image file."""
    image, format_str = validate_image_file(sample_image_file)
    assert image is not None
    assert isinstance(image, Image.Image)
    assert format_str in ["PNG", "JPEG"]


def test_validate_image_file_invalid_format():
    """Test validating an invalid image format."""
    invalid_data = io.BytesIO(b"not an image")
    with pytest.raises(ImageValidationError):
        validate_image_file(invalid_data)


def test_validate_image_file_too_large():
    """Test validating file size exceeding limits."""
    # Create a file that exceeds the limit
    large_data = b"x" * (settings.MAX_UPLOAD_SIZE + 1)
    large_file = io.BytesIO(large_data)
    with pytest.raises(ImageValidationError):
        validate_image_file(large_file)


def test_validate_image_file_too_small():
    """Test validating image with dimensions too small."""
    img = Image.new('RGB', (32, 32), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    with pytest.raises(ImageValidationError):
        validate_image_file(img_bytes)


def test_resize_image_max_size():
    """Test resizing image with max_size parameter."""
    img = Image.new('RGB', (3000, 2000), color='red')
    resized = resize_image(img, max_size=1024)
    
    assert resized.size[0] <= 1024
    assert resized.size[1] <= 1024
    assert resized.size[0] == 1024  # Should maintain aspect ratio


def test_resize_image_target_size():
    """Test resizing image with target_size parameter."""
    img = Image.new('RGB', (500, 500), color='green')
    resized = resize_image(img, target_size=(256, 256))
    
    assert resized.size == (256, 256)


def test_normalize_image_rgb():
    """Test normalizing RGB image."""
    img = Image.new('RGB', (100, 100), color='blue')
    normalized = normalize_image(img)
    assert normalized.mode == 'RGB'


def test_normalize_image_rgba():
    """Test normalizing RGBA image."""
    img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
    normalized = normalize_image(img)
    assert normalized.mode == 'RGB'

