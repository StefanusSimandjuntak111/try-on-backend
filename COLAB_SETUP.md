# Google Colab Setup Guide

This guide helps you set up and run the AI Try-On Backend project in Google Colab.

## Quick Start

1. **Open the Colab Notebook**
   - Upload `colab_setup.ipynb` to Google Colab
   - Or open it directly from GitHub

2. **Run the Setup Cells**
   - Execute cells in order
   - The notebook will:
     - Install all dependencies
     - Clone the repository
     - Setup GPU environment
     - Test ML models

## Manual Setup

If you prefer to set up manually:

### Step 1: Install Dependencies

```bash
# System dependencies
!apt-get update -qq
!apt-get install -y -qq libgl1-mesa-glx libglib2.0-0

# PyTorch with CUDA (for GPU support)
!pip install torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118

# Other dependencies
!pip install -r requirements-colab.txt
```

### Step 2: Clone Repository

```python
import os
import sys

# Clone repository
!git clone https://github.com/StefanusSimandjuntak111/try-on-backend.git /content/try-on-backend

# Add to Python path
sys.path.insert(0, '/content/try-on-backend')
os.chdir('/content/try-on-backend')
```

### Step 3: Setup Environment

```python
import torch
from pathlib import Path

# Check GPU
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device: {device}")

# Create directories
Path("weights").mkdir(exist_ok=True)
Path("uploads").mkdir(exist_ok=True)
Path("results").mkdir(exist_ok=True)
```

### Step 4: Test ML Models

```python
from app.config import settings
settings.ML_DEVICE = device

# Test models
from app.ml.background.model import get_u2net_model
from app.ml.parsing.model import get_schp_model
from app.ml.pose.model import get_openpose_model
from app.ml.hrviton.model import get_hrviton_model

u2net = get_u2net_model()
schp = get_schp_model()
openpose = get_openpose_model()
hrviton = get_hrviton_model()
```

## Running the API Server

### Option 1: Using ngrok (Recommended for Public Access)

```python
from pyngrok import ngrok

# Setup ngrok (get token from https://dashboard.ngrok.com)
NGROK_AUTHTOKEN = "your_token_here"  # Optional
if NGROK_AUTHTOKEN:
    ngrok.set_auth_token(NGROK_AUTHTOKEN)

# Start tunnel
public_url = ngrok.connect(8000)
print(f"Public URL: {public_url}")
```

Then start the server:

```python
import subprocess
import threading

def run_server():
    subprocess.run([
        "python", "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
```

### Option 2: Local Only

```python
!python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access the API at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

## Features in Colab

### ✅ GPU Support
- Automatic GPU detection
- CUDA-enabled PyTorch installation
- Models run on GPU if available

### ✅ Model Testing
- Test individual ML models
- Run inference on uploaded images
- Visualize results

### ✅ API Server
- Run FastAPI server in Colab
- Expose via ngrok for public access
- Full API documentation

### ⚠️ Limitations
- **No PostgreSQL/Redis**: Use SQLite for database (configured automatically)
- **No Celery Workers**: Background tasks won't work (use direct function calls)
- **Session Timeout**: Colab sessions timeout after inactivity
- **File Storage**: Files are temporary (use Google Drive for persistence)

## Using Google Drive for Persistence

To persist files across sessions:

```python
from google.colab import drive

# Mount Google Drive
drive.mount('/content/drive')

# Copy project to Drive
!cp -r /content/try-on-backend /content/drive/MyDrive/

# Or work directly from Drive
!cd /content/drive/MyDrive/try-on-backend
```

## Troubleshooting

### GPU Not Available
- Runtime → Change runtime type → GPU
- Check: `!nvidia-smi`

### Import Errors
- Make sure repository is cloned
- Check Python path: `import sys; print(sys.path)`
- Restart runtime if needed

### Port Already in Use
```python
# Kill existing process
!lsof -ti:8000 | xargs kill -9
```

### Model Weights Not Found
- Download weights manually or use the download script
- Place weights in `weights/` directory

## Next Steps

1. **Download Model Weights**: Use `scripts/download_weights.py`
2. **Test Models**: Run inference on sample images
3. **Deploy API**: Use ngrok to expose API publicly
4. **Integrate**: Connect your frontend to the Colab API

## Resources

- [Project Repository](https://github.com/StefanusSimandjuntak111/try-on-backend)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [ngrok Documentation](https://ngrok.com/docs)

