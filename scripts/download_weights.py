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

# Try to import gdown for Google Drive downloads
try:
    import gdown
    GDOWN_AVAILABLE = True
except ImportError:
    GDOWN_AVAILABLE = False
    logger.warning("gdown not installed. Install with: pip install gdown")

# Model URLs and repository links
# Note: Many models are hosted on Google Drive which requires special handling
# For direct download, use gdown or manual download from the repositories

MODEL_URLS = {
    "hrviton": {
        "url": None,  # Google Drive link - use repository instructions
        "filename": "hrviton.pth",
        "description": "HR-VITON try-on model",
        "repository": "https://github.com/sangyun884/HR-VITON#pretrained-models",
        "instructions": "Download from official repository: https://github.com/sangyun884/HR-VITON#pretrained-models",
        "google_drive_id": None,  # Check repository for current Google Drive ID
    },
    "schp": {
        "url": None,  # Google Drive link - use repository instructions
        "filename": "lip_final.pth",  # SCHP uses lip_final.pth as the main model
        "description": "SCHP human parsing model",
        "repository": "https://github.com/GoGoDuck912/Self-Correction-Human-Parsing#trained-models",
        "instructions": "Download from official repository: https://github.com/GoGoDuck912/Self-Correction-Human-Parsing#trained-models",
        "google_drive_id": None,  # Check repository for current Google Drive ID
    },
    "openpose": {
        "url": None,  # Direct download from repository
        "filename": "body_pose_model.pth",
        "description": "OpenPose pose estimation model",
        "repository": "https://github.com/Hzzone/pytorch-openpose#download-models",
        "instructions": "Download from official repository: https://github.com/Hzzone/pytorch-openpose#download-models",
        "google_drive_id": None,  # Check repository for current download link
    },
    "u2net": {
        "url": "https://drive.google.com/uc?id=1ao1ovg1p6Qd1oVA48TlQKH51sdCEd_Ei",  # Google Drive direct link
        "filename": "u2net.pth",
        "description": "U2-Net background removal model (176.3 MB)",
        "repository": "https://github.com/xuebinqin/U-2-Net#usage-for-salient-object-detection",
        "instructions": "Official repository: https://github.com/xuebinqin/U-2-Net",
        "google_drive_id": "1ao1ovg1p6Qd1oVA48TlQKH51sdCEd_Ei",
    },
}

# Alternative: U2-Net lightweight version
U2NET_LIGHT = {
    "url": "https://drive.google.com/uc?id=1rbSTGKAE-MTxBYHd-51lZHh6S1bT3g",  # u2netp.pth
    "filename": "u2netp.pth",
    "description": "U2-Net lightweight model (4.7 MB)",
    "google_drive_id": "1rbSTGKAE-MTxBYHd-51lZHh6S1bT3g",
}


def download_file(url: str, filepath: Path, description: str = "", google_drive_id: str = None) -> bool:
    """Download a file with progress bar.

    Args:
        url: URL to download from (None for Google Drive)
        filepath: Path to save file
        description: Description for progress bar
        google_drive_id: Google Drive file ID (for gdown)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Use gdown for Google Drive files
        if google_drive_id and GDOWN_AVAILABLE:
            logger.info("Downloading from Google Drive", file_id=google_drive_id)
            gdown_url = f"https://drive.google.com/uc?id={google_drive_id}"
            gdown.download(gdown_url, str(filepath), quiet=False)
            if filepath.exists():
                logger.info("Downloaded file", filepath=str(filepath))
                return True
            else:
                logger.error("Download failed - file not found")
                return False
        
        # Fallback to direct URL download
        if not url:
            logger.error("No URL or Google Drive ID provided")
            return False
            
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


def download_weights(model_name: str = None, show_instructions: bool = False) -> None:
    """Download model weights.

    Args:
        model_name: Specific model to download (None for all)
        show_instructions: Show manual download instructions for models without direct URLs
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
        
        # Check if manual download is needed
        if model_info["url"] is None and model_info.get("google_drive_id") is None:
            logger.warning(
                "Manual download required",
                model=model_key,
                repository=model_info.get("repository", "N/A")
            )
            if show_instructions:
                print(f"\n{'='*60}")
                print(f"Manual download required for {model_key}")
                print(f"Repository: {model_info.get('repository', 'N/A')}")
                print(f"Instructions: {model_info.get('instructions', 'N/A')}")
                print(f"Save file as: {filepath}")
                print(f"{'='*60}\n")
            continue
        
        logger.info("Downloading model", model=model_key, url=model_info.get("url", "Google Drive"))
        success = download_file(
            model_info.get("url"),
            filepath,
            description=model_info["description"],
            google_drive_id=model_info.get("google_drive_id"),
        )
        
        if success:
            logger.info("Model downloaded successfully", model=model_key)
        else:
            logger.error("Failed to download model", model=model_key)
            if show_instructions:
                print(f"\nManual download may be required:")
                print(f"Repository: {model_info.get('repository', 'N/A')}")
                print(f"Save file as: {filepath}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download pretrained model weights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Official Repository Links:
  HR-VITON:   https://github.com/sangyun884/HR-VITON#pretrained-models
  SCHP:       https://github.com/GoGoDuck912/Self-Correction-Human-Parsing#trained-models
  OpenPose:   https://github.com/Hzzone/pytorch-openpose#download-models
  U2-Net:     https://github.com/xuebinqin/U-2-Net#usage-for-salient-object-detection

Note: Some models require manual download from their repositories.
      Install gdown for Google Drive downloads: pip install gdown
        """
    )
    parser.add_argument(
        "--model",
        type=str,
        choices=list(MODEL_URLS.keys()),
        help="Specific model to download (default: all)",
    )
    parser.add_argument(
        "--show-instructions",
        action="store_true",
        help="Show manual download instructions for models without direct URLs",
    )
    
    args = parser.parse_args()
    download_weights(args.model, show_instructions=args.show_instructions)

