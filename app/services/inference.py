"""ML inference service orchestrating all models."""

from typing import Optional

from PIL import Image

from app.core.logging import get_logger
from app.ml.background.model import get_u2net_model
from app.ml.hrviton.model import get_hrviton_model
from app.ml.parsing.model import get_schp_model
from app.ml.pose.model import get_openpose_model

logger = get_logger(__name__)


class InferenceService:
    """Service for orchestrating ML model inference."""

    def __init__(self):
        """Initialize inference service."""
        self.u2net = get_u2net_model()
        self.schp = get_schp_model()
        self.openpose = get_openpose_model()
        self.hrviton = get_hrviton_model()
        logger.info("Inference service initialized")

    def preprocess_model(
        self, model_image: Image.Image
    ) -> dict:
        """Preprocess model image with all required ML models.

        Args:
            model_image: Model image (RGB)

        Returns:
            Dictionary with preprocessing results:
                - 'image': Preprocessed image
                - 'background_removed': Image with background removed
                - 'parsing': Human parsing result
                - 'pose': Pose estimation result
                - 'metadata': Processing metadata
        """
        logger.info("Preprocessing model image")
        
        results = {
            "image": model_image,
            "metadata": {},
        }
        
        try:
            # 1. Background removal
            logger.debug("Removing background")
            background_removed = self.u2net.remove_background(model_image)
            results["background_removed"] = background_removed
            results["metadata"]["background_removed"] = True
        except Exception as e:
            logger.warning("Background removal failed", error=str(e))
            results["background_removed"] = model_image
            results["metadata"]["background_removed"] = False
        
        try:
            # 2. Human parsing
            logger.debug("Parsing human")
            parsing_result = self.schp.parse(model_image)
            results["parsing"] = parsing_result
            results["metadata"]["parsing_complete"] = True
        except Exception as e:
            logger.warning("Human parsing failed", error=str(e))
            results["parsing"] = None
            results["metadata"]["parsing_complete"] = False
        
        try:
            # 3. Pose estimation
            logger.debug("Estimating pose")
            pose_result = self.openpose.estimate_pose(model_image)
            results["pose"] = pose_result
            results["metadata"]["pose_estimated"] = True
        except Exception as e:
            logger.warning("Pose estimation failed", error=str(e))
            results["pose"] = None
            results["metadata"]["pose_estimated"] = False
        
        logger.info("Model preprocessing completed", metadata=results["metadata"])
        return results

    def preprocess_garment(
        self, garment_image: Image.Image
    ) -> dict:
        """Preprocess garment image.

        Args:
            garment_image: Garment image (RGB)

        Returns:
            Dictionary with preprocessing results:
                - 'image': Preprocessed image
                - 'background_removed': Image with background removed
                - 'mask': Garment segmentation mask
                - 'metadata': Processing metadata
        """
        logger.info("Preprocessing garment image")
        
        results = {
            "image": garment_image,
            "metadata": {},
        }
        
        try:
            # 1. Background removal
            logger.debug("Removing garment background")
            background_removed = self.u2net.remove_background(garment_image)
            results["background_removed"] = background_removed
            results["metadata"]["background_removed"] = True
            
            # 2. Get garment mask
            mask = self.u2net.get_mask(garment_image)
            results["mask"] = mask
            results["metadata"]["mask_generated"] = True
            
        except Exception as e:
            logger.warning("Garment preprocessing failed", error=str(e))
            results["background_removed"] = garment_image
            results["mask"] = None
            results["metadata"]["background_removed"] = False
            results["metadata"]["mask_generated"] = False
        
        logger.info("Garment preprocessing completed", metadata=results["metadata"])
        return results

    def perform_tryon(
        self,
        model_image: Image.Image,
        garment_image: Image.Image,
        model_preprocessing: Optional[dict] = None,
        garment_preprocessing: Optional[dict] = None,
    ) -> Image.Image:
        """Perform virtual try-on inference.

        Args:
            model_image: Model image (RGB)
            garment_image: Garment image (RGB)
            model_preprocessing: Optional pre-computed model preprocessing
            garment_preprocessing: Optional pre-computed garment preprocessing

        Returns:
            Try-on result image (RGB)
        """
        logger.info("Performing try-on inference")
        
        # Use pre-computed preprocessing if available
        model_parsing = None
        model_pose = None
        garment_mask = None
        
        if model_preprocessing:
            model_parsing = model_preprocessing.get("parsing")
            model_pose = model_preprocessing.get("pose")
        
        if garment_preprocessing:
            garment_mask = garment_preprocessing.get("mask")
        
        # Perform try-on
        try:
            result_image = self.hrviton.tryon(
                model_image=model_image,
                garment_image=garment_image,
                model_parsing=model_parsing,
                model_pose=model_pose,
                garment_mask=garment_mask,
            )
            
            logger.info("Try-on inference completed", size=result_image.size)
            return result_image
            
        except Exception as e:
            logger.error("Try-on inference failed", error=str(e))
            raise


# Global inference service instance
inference_service = InferenceService()

