"""Download pretrained model weights."""

import os
import sys
from pathlib import Path

import requests
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Model URLs (placeholder - replace with actual URLs)
MODEL_URLS = {
    "hrviton": {
        "url": "https://example.com/weights/hrviton.pth",
        "filename": "hrviton.pth",
        "description": "HR-VITON try-on model",
    },
    "schp": {
        "url": "https://example.com/weights/schp.pth",
        "filename": "schp.pth",
        "description": "SCHP human parsing model",
    },
    "openpose": {
        "url": "https://example.com/weights/openpose.pth",
        "filename": "openpose.pth",
        "description": "OpenPose model",
    },
    "u2net": {
        "url": "https://example.com/weights/u2net.pth",
        "filename": "u2net.pth",
        "description": "U2-Net background removal model",
    },
}


def download_file(url: str, filepath: Path, description: str = "") -> bool:
    """Download a file with progress bar.

    Args:
        url: URL to download from
        filepath: Path to save file
        description: Description for progress bar

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get("content-length", 0))
        
        with open(filepath, "wb") as f:
            with tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=description or filepath.name,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        logger.info("Downloaded file", filepath=str(filepath), size=total_size)
        return True
        
    except Exception as e:
        logger.error("Failed to download file", url=url, error=str(e))
        return False


def download_weights(model_name: str = None) -> None:
    """Download model weights.

    Args:
        model_name: Specific model to download (None for all)
    """
    # Create weights directory
    weights_dir = Path("weights")
    weights_dir.mkdir(exist_ok=True)
    
    models_to_download = [model_name] if model_name else MODEL_URLS.keys()
    
    for model_key in models_to_download:
        if model_key not in MODEL_URLS:
            logger.warning("Unknown model", model=model_key)
            continue
        
        model_info = MODEL_URLS[model_key]
        filepath = weights_dir / model_info["filename"]
        
        # Skip if already exists
        if filepath.exists():
            logger.info("Model already exists", model=model_key, filepath=str(filepath))
            response = input(f"Overwrite {model_key}? (y/N): ")
            if response.lower() != "y":
                continue
        
        logger.info("Downloading model", model=model_key, url=model_info["url"])
        success = download_file(
            model_info["url"],
            filepath,
            description=model_info["description"],
        )
        
        if success:
            logger.info("Model downloaded successfully", model=model_key)
        else:
            logger.error("Failed to download model", model=model_key)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Download pretrained model weights")
    parser.add_argument(
        "--model",
        type=str,
        choices=list(MODEL_URLS.keys()),
        help="Specific model to download (default: all)",
    )
    
    args = parser.parse_args()
    download_weights(args.model)

