# Model Weights Download Guide

This guide provides instructions for downloading the required model weights for the AI Try-On Backend.

## Quick Start

Install gdown for Google Drive downloads:
```bash
pip install gdown
```

Download all available models:
```bash
python scripts/download_weights.py
```

Download specific model:
```bash
python scripts/download_weights.py --model u2net
```

## Official Repository Links

### HR-VITON
- **Repository**: https://github.com/sangyun884/HR-VITON#pretrained-models
- **File**: `hrviton.pth`
- **Instructions**: Check the repository README for the latest Google Drive download link
- **Status**: Manual download required (URL may change)

### SCHP (Self-Correction Human Parsing)
- **Repository**: https://github.com/GoGoDuck912/Self-Correction-Human-Parsing#trained-models
- **File**: `lip_final.pth` (or `exp-schp-201908261155-lip.pth`)
- **Instructions**: Check the repository README for download links
- **Status**: Manual download required (URL may change)

### OpenPose
- **Repository**: https://github.com/Hzzone/pytorch-openpose#download-models
- **File**: `body_pose_model.pth`
- **Instructions**: Check the repository README for download links
- **Status**: Manual download required (URL may change)

### U2-Net
- **Repository**: https://github.com/xuebinqin/U-2-Net#usage-for-salient-object-detection
- **File**: `u2net.pth` (176.3 MB) or `u2netp.pth` (4.7 MB for lightweight)
- **Google Drive**: Direct download available
- **Status**: ✅ Automatic download supported

## Manual Download Instructions

### For Google Drive Files

1. **Using gdown** (recommended):
   ```bash
   pip install gdown
   gdown --id <GOOGLE_DRIVE_ID> -O weights/<filename>.pth
   ```

2. **Using wget** (if direct link available):
   ```bash
   wget -O weights/<filename>.pth "https://drive.google.com/uc?id=<GOOGLE_DRIVE_ID>"
   ```

3. **Manual download**:
   - Visit the repository README
   - Click on the Google Drive link
   - Download the file manually
   - Place it in the `weights/` directory

### File Structure

After downloading, your `weights/` directory should look like:
```
weights/
├── u2net.pth          # U2-Net background removal
├── hrviton.pth        # HR-VITON try-on model
├── lip_final.pth      # SCHP human parsing
└── body_pose_model.pth # OpenPose pose estimation
```

## Download Script Usage

```bash
# Download all available models
python scripts/download_weights.py

# Download specific model
python scripts/download_weights.py --model u2net

# Show manual download instructions
python scripts/download_weights.py --show-instructions

# Download specific model with instructions
python scripts/download_weights.py --model hrviton --show-instructions
```

## Troubleshooting

### Google Drive Download Fails

If automatic download fails:
1. Check if the file ID is correct
2. Verify internet connection
3. Try manual download from repository
4. Some files may require authentication

### File Not Found

If a model file is not found:
1. Check the official repository for updated links
2. Verify the filename matches expectations
3. Some repositories may have changed their file structure

### Permission Denied

If you get permission errors:
1. Ensure you have write permissions in the `weights/` directory
2. Check disk space availability
3. Some files are large (100+ MB), ensure sufficient space

## Model Sizes

Approximate file sizes:
- `u2net.pth`: ~176 MB
- `u2netp.pth`: ~4.7 MB (lightweight)
- `hrviton.pth`: ~500 MB (varies)
- `lip_final.pth`: ~200 MB (varies)
- `body_pose_model.pth`: ~200 MB (varies)

## Notes

- **U2-Net**: Direct download is supported via the script
- **HR-VITON, SCHP, OpenPose**: May require manual download as URLs can change
- Always check the official repositories for the latest download links
- Some models may require specific versions or configurations

## For Google Colab

In Colab, you can download weights directly:

```python
# Install gdown
!pip install gdown

# Download U2-Net
!gdown --id 1ao1ovg1p6Qd1oVA48TlQKH51sdCEd_Ei -O weights/u2net.pth

# For other models, check repository for current Google Drive IDs
```

## Updating Weights

To update model weights:
1. Check the official repository for new versions
2. Update the download script with new URLs/IDs
3. Re-download the weights

## Support

If you encounter issues:
1. Check the official repository README
2. Open an issue on the respective repository
3. Verify the file format matches what the code expects

