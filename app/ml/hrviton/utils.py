"""HR-VITON utility functions."""

import numpy as np
from PIL import Image
import torch


def align_images(model_image: Image.Image, garment_image: Image.Image) -> tuple[Image.Image, Image.Image]:
    """Align model and garment images for try-on.

    Args:
        model_image: Model image (RGB)
        garment_image: Garment image (RGB)

    Returns:
        Tuple of (aligned_model_image, aligned_garment_image)
    """
    # Standard size for HR-VITON
    target_size = (768, 1024)
    
    # Resize model image
    model_aligned = model_image.resize(target_size, Image.Resampling.LANCZOS)
    
    # For garment, we might want to preserve aspect ratio but fit to a region
    # This is simplified - actual HR-VITON may have more complex alignment
    garment_aligned = garment_image.resize(target_size, Image.Resampling.LANCZOS)
    
    return model_aligned, garment_aligned


def normalize_tensor(tensor: torch.Tensor) -> torch.Tensor:
    """Normalize tensor to [-1, 1] range.

    Args:
        tensor: Input tensor (0-255 range)

    Returns:
        Normalized tensor (-1 to 1 range)
    """
    return (tensor / 127.5) - 1.0


def denormalize_tensor(tensor: torch.Tensor) -> torch.Tensor:
    """Denormalize tensor from [-1, 1] to [0, 255] range.

    Args:
        tensor: Normalized tensor (-1 to 1 range)

    Returns:
        Denormalized tensor (0 to 255 range)
    """
    return (tensor + 1.0) * 127.5


def image_to_tensor(image: Image.Image, normalize: bool = True) -> torch.Tensor:
    """Convert PIL Image to tensor.

    Args:
        image: PIL Image (RGB)
        normalize: Whether to normalize to [-1, 1]

    Returns:
        Tensor (1, 3, H, W)
    """
    # Convert to numpy
    img_array = np.array(image).astype(np.float32)
    
    # Convert to tensor
    tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
    
    if normalize:
        tensor = normalize_tensor(tensor)
    
    return tensor


def tensor_to_image(tensor: torch.Tensor, denormalize: bool = True) -> Image.Image:
    """Convert tensor to PIL Image.

    Args:
        tensor: Tensor (1, 3, H, W) or (3, H, W)
        denormalize: Whether to denormalize from [-1, 1]

    Returns:
        PIL Image (RGB)
    """
    # Remove batch dimension if present
    if tensor.dim() == 4:
        tensor = tensor.squeeze(0)
    
    if denormalize:
        tensor = denormalize_tensor(tensor)
    
    # Clamp to valid range
    tensor = torch.clamp(tensor, 0, 255)
    
    # Convert to numpy
    img_array = tensor.permute(1, 2, 0).cpu().numpy().astype(np.uint8)
    
    return Image.fromarray(img_array, mode="RGB")


def create_agnostic_mask(
    parsing_mask: np.ndarray,
    pose_keypoints: list,
    image_size: tuple[int, int],
) -> np.ndarray:
    """Create agnostic mask for try-on (removes garment area).

    Args:
        parsing_mask: Human parsing mask
        pose_keypoints: Pose keypoints
        image_size: Image size (width, height)

    Returns:
        Agnostic mask (binary)
    """
    # Simplified agnostic mask creation
    # In practice, this would be more complex based on HR-VITON's requirements
    mask = np.ones(image_size[::-1], dtype=np.uint8) * 255
    
    # Remove upper clothes area (if detected in parsing)
    # This is simplified - actual implementation would be more sophisticated
    upper_clothes_label = 5  # upper-clothes label
    mask[parsing_mask == upper_clothes_label] = 0
    
    return mask


def postprocess_tryon_result(result_tensor: torch.Tensor) -> Image.Image:
    """Postprocess try-on result tensor to image.

    Args:
        result_tensor: Try-on result tensor

    Returns:
        Final result image
    """
    image = tensor_to_image(result_tensor)
    
    # Additional post-processing if needed
    # e.g., blending, smoothing, etc.
    
    return image

