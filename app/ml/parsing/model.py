"""SCHP (Self-Correction Human Parsing) model integration."""

from typing import Optional

import numpy as np
import torch
from PIL import Image

from app.config import settings
from app.core.exceptions import ProcessingError
from app.core.logging import get_logger

logger = get_logger(__name__)

# SCHP parsing labels (standard LIP dataset labels)
SCHP_LABELS = {
    0: "background",
    1: "hat",
    2: "hair",
    3: "glove",
    4: "sunglasses",
    5: "upper-clothes",
    6: "dress",
    7: "coat",
    8: "socks",
    9: "pants",
    10: "jumpsuits",
    11: "scarf",
    12: "skirt",
    13: "face",
    14: "left-arm",
    15: "right-arm",
    16: "left-leg",
    17: "right-leg",
    18: "left-shoe",
    19: "right-shoe",
}


class SCHPModel:
    """SCHP model for human parsing."""

    def __init__(self, checkpoint_path: Optional[str] = None):
        """Initialize SCHP model.

        Args:
            checkpoint_path: Path to model checkpoint (default from settings)
        """
        self.checkpoint_path = checkpoint_path or settings.SCHP_CHECKPOINT
        self.device = torch.device(settings.ML_DEVICE if torch.cuda.is_available() else "cpu")
        self.model = None
        self.num_classes = 20  # LIP dataset has 20 classes
        self._load_model()

    def _load_model(self) -> None:
        """Load SCHP model from checkpoint."""
        try:
            logger.info("Loading SCHP model", checkpoint=self.checkpoint_path, device=str(self.device))
            
            # TODO: Implement actual SCHP model loading
            # from schp import SCHP
            # self.model = SCHP(num_classes=self.num_classes)
            # self.model.load_state_dict(torch.load(self.checkpoint_path, map_location=self.device))
            # self.model.to(self.device)
            # self.model.eval()
            
            logger.warning("SCHP model loading not implemented - using placeholder")
            self.model = None  # Placeholder
            
        except Exception as e:
            logger.error("Failed to load SCHP model", error=str(e))
            raise ProcessingError(f"Failed to load SCHP model: {str(e)}")

    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for SCHP.

        Args:
            image: PIL Image (RGB)

        Returns:
            Preprocessed tensor (1, 3, H, W)
        """
        # Resize to 473x473 (SCHP input size)
        image = image.resize((473, 473), Image.Resampling.LANCZOS)
        
        # Convert to numpy and normalize
        img_array = np.array(image).astype(np.float32)
        
        # Normalize: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_array = (img_array / 255.0 - mean) / std
        
        # Convert to tensor
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).unsqueeze(0)
        
        return img_tensor.to(self.device)

    def parse(self, image: Image.Image) -> dict:
        """Parse human image into body parts.

        Args:
            image: PIL Image (RGB)

        Returns:
            Dictionary with:
                - 'mask': Parsing mask as PIL Image
                - 'segments': Dictionary of body part masks
                - 'labels': List of detected labels
        """
        if self.model is None:
            logger.warning("SCHP model not loaded, returning placeholder parsing")
            return self._placeholder_parsing(image)
        
        try:
            original_size = image.size
            input_tensor = self.preprocess_image(image)
            
            # Inference
            with torch.no_grad():
                output = self.model(input_tensor)
                # Get prediction
                pred = torch.argmax(output[0], dim=1).squeeze().cpu().numpy()
            
            # Resize prediction to original size
            pred_pil = Image.fromarray(pred.astype(np.uint8), mode="L")
            pred_pil = pred_pil.resize(original_size, Image.Resampling.NEAREST)
            pred_array = np.array(pred_pil)
            
            # Extract individual body parts
            segments = {}
            labels = []
            
            for label_id, label_name in SCHP_LABELS.items():
                mask = (pred_array == label_id).astype(np.uint8) * 255
                if mask.sum() > 0:  # Only include if segment exists
                    segments[label_name] = Image.fromarray(mask, mode="L")
                    labels.append(label_name)
            
            result = {
                "mask": pred_pil,
                "segments": segments,
                "labels": labels,
                "parsing_map": pred_array,
            }
            
            logger.debug("Human parsing completed", labels=len(labels), size=original_size)
            return result
            
        except Exception as e:
            logger.error("Failed to parse human", error=str(e))
            return self._placeholder_parsing(image)

    def _placeholder_parsing(self, image: Image.Image) -> dict:
        """Placeholder parsing (returns full body mask).

        Args:
            image: PIL Image

        Returns:
            Placeholder parsing result
        """
        # Create a simple full-body mask
        mask = np.ones((image.size[1], image.size[0]), dtype=np.uint8) * 13  # Face label
        mask_pil = Image.fromarray(mask, mode="L")
        
        return {
            "mask": mask_pil,
            "segments": {"face": mask_pil},
            "labels": ["face"],
            "parsing_map": mask,
        }

    def get_body_mask(self, image: Image.Image) -> Image.Image:
        """Get binary mask of human body (excluding background).

        Args:
            image: PIL Image (RGB)

        Returns:
            Binary body mask as PIL Image (L mode)
        """
        parsing_result = self.parse(image)
        mask = parsing_result["mask"]
        
        # Convert to binary (non-zero = body)
        mask_array = np.array(mask)
        binary_mask = (mask_array > 0).astype(np.uint8) * 255
        
        return Image.fromarray(binary_mask, mode="L")

    def get_upper_clothes_mask(self, image: Image.Image) -> Image.Image:
        """Get mask for upper clothes area.

        Args:
            image: PIL Image (RGB)

        Returns:
            Upper clothes mask as PIL Image (L mode)
        """
        parsing_result = self.parse(image)
        segments = parsing_result["segments"]
        
        # Combine upper-clothes related segments
        upper_labels = ["upper-clothes", "coat", "dress", "jumpsuits"]
        
        mask_array = None
        for label in upper_labels:
            if label in segments:
                seg_array = np.array(segments[label])
                if mask_array is None:
                    mask_array = seg_array
                else:
                    mask_array = np.maximum(mask_array, seg_array)
        
        if mask_array is None:
            # Return empty mask if no upper clothes found
            mask_array = np.zeros((image.size[1], image.size[0]), dtype=np.uint8)
        
        return Image.fromarray(mask_array, mode="L")


# Global model instance (lazy loading)
_schp_model: Optional[SCHPModel] = None


def get_schp_model() -> SCHPModel:
    """Get global SCHP model instance."""
    global _schp_model
    if _schp_model is None:
        _schp_model = SCHPModel()
    return _schp_model

