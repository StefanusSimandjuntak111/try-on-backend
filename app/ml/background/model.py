"""U2-Net background removal model integration."""

import io
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from PIL import Image

from app.config import settings
from app.core.exceptions import ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class U2NetModel:
    """U2-Net model for background removal."""

    def __init__(self, checkpoint_path: Optional[str] = None):
        """Initialize U2-Net model.

        Args:
            checkpoint_path: Path to model checkpoint (default from settings)
        """
        self.checkpoint_path = checkpoint_path or settings.U2NET_CHECKPOINT
        self.device = torch.device(settings.ML_DEVICE if torch.cuda.is_available() else "cpu")
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Load U2-Net model from checkpoint."""
        try:
            # TODO: Implement actual U2-Net model architecture
            # This is a placeholder structure
            # You'll need to import or define the U2Net architecture
            logger.info("Loading U2-Net model", checkpoint=self.checkpoint_path, device=str(self.device))
            
            # Placeholder: Replace with actual model loading
            # from u2net import U2NET
            # self.model = U2NET(in_ch=3, out_ch=1)
            # self.model.load_state_dict(torch.load(self.checkpoint_path, map_location=self.device))
            # self.model.to(self.device)
            # self.model.eval()
            
            logger.warning("U2-Net model loading not implemented - using placeholder")
            self.model = None  # Placeholder
            
        except Exception as e:
            logger.error("Failed to load U2-Net model", error=str(e))
            raise ProcessingError(f"Failed to load U2-Net model: {str(e)}")

    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for U2-Net.

        Args:
            image: PIL Image (RGB)

        Returns:
            Preprocessed tensor (1, 3, H, W)
        """
        # Resize to 320x320 (U2-Net input size)
        image = image.resize((320, 320), Image.Resampling.LANCZOS)
        
        # Convert to numpy array and normalize
        img_array = np.array(image).astype(np.float32) / 255.0
        
        # Convert to tensor and add batch dimension
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
        
        return img_tensor.to(self.device)

    def remove_background(self, image: Image.Image) -> Image.Image:
        """Remove background from image using U2-Net.

        Args:
            image: PIL Image (RGB)

        Returns:
            PIL Image with transparent background (RGBA)
        """
        if self.model is None:
            logger.warning("U2-Net model not loaded, returning original image")
            # Fallback: return image with white background removed (simple threshold)
            return self._simple_background_removal(image)
        
        try:
            # Preprocess
            input_tensor = self.preprocess_image(image)
            
            # Inference
            with torch.no_grad():
                output = self.model(input_tensor)
                # U2-Net outputs multiple scales, use the main one
                mask = output[0] if isinstance(output, (list, tuple)) else output
                mask = torch.sigmoid(mask)
            
            # Postprocess mask
            mask_np = mask.squeeze().cpu().numpy()
            mask_np = (mask_np * 255).astype(np.uint8)
            
            # Resize mask to original image size
            mask_pil = Image.fromarray(mask_np, mode="L")
            mask_pil = mask_pil.resize(image.size, Image.Resampling.LANCZOS)
            
            # Apply mask to original image
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            
            # Create alpha channel from mask
            alpha = mask_pil
            image.putalpha(alpha)
            
            logger.debug("Background removed", size=image.size)
            return image
            
        except Exception as e:
            logger.error("Failed to remove background", error=str(e))
            # Fallback to simple method
            return self._simple_background_removal(image)

    def _simple_background_removal(self, image: Image.Image) -> Image.Image:
        """Simple background removal fallback (removes white background).

        Args:
            image: PIL Image

        Returns:
            Image with transparent background
        """
        # Convert to RGBA
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        
        # Simple white background removal
        data = np.array(image)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        
        # Threshold for white background
        white_threshold = 240
        mask = (r > white_threshold) & (g > white_threshold) & (b > white_threshold)
        
        # Set alpha channel
        a[mask] = 0
        data[:, :, 3] = a
        
        return Image.fromarray(data, mode="RGBA")

    def get_mask(self, image: Image.Image) -> Image.Image:
        """Get binary mask of foreground.

        Args:
            image: PIL Image (RGB)

        Returns:
            Binary mask as PIL Image (L mode)
        """
        if self.model is None:
            logger.warning("U2-Net model not loaded")
            # Return simple mask
            mask = np.ones((image.size[1], image.size[0]), dtype=np.uint8) * 255
            return Image.fromarray(mask, mode="L")
        
        try:
            input_tensor = self.preprocess_image(image)
            
            with torch.no_grad():
                output = self.model(input_tensor)
                mask = output[0] if isinstance(output, (list, tuple)) else output
                mask = torch.sigmoid(mask)
            
            mask_np = mask.squeeze().cpu().numpy()
            mask_np = (mask_np * 255).astype(np.uint8)
            
            mask_pil = Image.fromarray(mask_np, mode="L")
            mask_pil = mask_pil.resize(image.size, Image.Resampling.LANCZOS)
            
            return mask_pil
            
        except Exception as e:
            logger.error("Failed to generate mask", error=str(e))
            # Return full mask as fallback
            mask = np.ones((image.size[1], image.size[0]), dtype=np.uint8) * 255
            return Image.fromarray(mask, mode="L")


# Global model instance (lazy loading)
_u2net_model: Optional[U2NetModel] = None


def get_u2net_model() -> U2NetModel:
    """Get global U2-Net model instance."""
    global _u2net_model
    if _u2net_model is None:
        _u2net_model = U2NetModel()
    return _u2net_model

