"""Test ML model inference."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image

from app.core.logging import setup_logging, get_logger
from app.services.inference import inference_service

setup_logging()
logger = get_logger(__name__)


def test_background_removal(image_path: str) -> None:
    """Test background removal."""
    logger.info("Testing background removal", image=image_path)
    
    image = Image.open(image_path).convert("RGB")
    result = inference_service.u2net.remove_background(image)
    
    output_path = "test_output_background_removed.png"
    result.save(output_path)
    logger.info("Background removal test completed", output=output_path)


def test_human_parsing(image_path: str) -> None:
    """Test human parsing."""
    logger.info("Testing human parsing", image=image_path)
    
    image = Image.open(image_path).convert("RGB")
    result = inference_service.schp.parse(image)
    
    logger.info("Human parsing test completed", labels=result.get("labels", []))
    
    # Save parsing mask
    if "mask" in result:
        result["mask"].save("test_output_parsing_mask.png")


def test_pose_estimation(image_path: str) -> None:
    """Test pose estimation."""
    logger.info("Testing pose estimation", image=image_path)
    
    image = Image.open(image_path).convert("RGB")
    result = inference_service.openpose.estimate_pose(image)
    
    logger.info(
        "Pose estimation test completed",
        keypoints=result.get("num_keypoints", 0),
    )


def test_tryon(model_path: str, garment_path: str) -> None:
    """Test try-on inference."""
    logger.info("Testing try-on", model=model_path, garment=garment_path)
    
    model_image = Image.open(model_path).convert("RGB")
    garment_image = Image.open(garment_path).convert("RGB")
    
    # Preprocess
    model_preprocessing = inference_service.preprocess_model(model_image)
    garment_preprocessing = inference_service.preprocess_garment(garment_image)
    
    # Perform try-on
    result = inference_service.perform_tryon(
        model_image,
        garment_image,
        model_preprocessing,
        garment_preprocessing,
    )
    
    output_path = "test_output_tryon.png"
    result.save(output_path)
    logger.info("Try-on test completed", output=output_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ML model inference")
    parser.add_argument("--test", type=str, choices=["background", "parsing", "pose", "tryon"])
    parser.add_argument("--image", type=str, help="Path to test image")
    parser.add_argument("--model", type=str, help="Path to model image (for tryon)")
    parser.add_argument("--garment", type=str, help="Path to garment image (for tryon)")
    
    args = parser.parse_args()
    
    if args.test == "background":
        if not args.image:
            print("Error: --image required for background test")
            sys.exit(1)
        test_background_removal(args.image)
    elif args.test == "parsing":
        if not args.image:
            print("Error: --image required for parsing test")
            sys.exit(1)
        test_human_parsing(args.image)
    elif args.test == "pose":
        if not args.image:
            print("Error: --image required for pose test")
            sys.exit(1)
        test_pose_estimation(args.image)
    elif args.test == "tryon":
        if not args.model or not args.garment:
            print("Error: --model and --garment required for tryon test")
            sys.exit(1)
        test_tryon(args.model, args.garment)
    else:
        print("Error: --test required")
        sys.exit(1)

