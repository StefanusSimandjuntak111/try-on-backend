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

**IMPORTANT:** Start the server FIRST, then connect ngrok. The server must be running before ngrok can connect.

**Step 1: Start the server**

```python
import subprocess
import time
import requests
from multiprocessing import Process

def run_server():
    """Run FastAPI server in a separate process."""
    import os
    os.environ["ML_DEVICE"] = "cuda" if torch.cuda.is_available() else "cpu"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"
    
    # Run uvicorn server
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )

# Start server in background process
print("🚀 Starting FastAPI server...")
server_process = Process(target=run_server, daemon=True)
server_process.start()

# Wait for server to start
print("⏳ Waiting for server to start...")
for i in range(30):
    try:
        response = requests.get("http://localhost:9000/", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running!")
            break
    except:
        if i < 29:
            time.sleep(1)
        else:
            raise Exception("Server did not start within 30 seconds")
```

**Step 2: Connect ngrok (AFTER server is running)**

```python
from pyngrok import ngrok

# Setup ngrok (get token from https://dashboard.ngrok.com)
NGROK_AUTHTOKEN = "your_token_here"  # Optional
if NGROK_AUTHTOKEN:
    ngrok.set_auth_token(NGROK_AUTHTOKEN)

# Verify server is running
response = requests.get("http://localhost:9000/", timeout=2)
if response.status_code == 200:
    # Start ngrok tunnel
    public_url = ngrok.connect(8000, bind_tls=True)
    print(f"🌐 Public URL: {public_url}")
    print(f"📚 API Docs: {public_url}/docs")
else:
    print("❌ Server is not running. Please start it first.")
```

### Option 2: Local Only

```python
!python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Access the API at:
- API: `http://localhost:9000`
- Docs: `http://localhost:9000/docs`

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
!lsof -ti:9000 | xargs kill -9
```

### ngrok Connection Refused (ERR_NGROK_8012)

This error means ngrok can't connect to the server. **The server must be running BEFORE connecting ngrok.**

**Solution:**
1. Make sure you've run the server cell first
2. Wait for "✅ Server is running!" message
3. Then run the ngrok cell
4. Verify server is running: `requests.get("http://localhost:9000/")`

**Check if server is running:**
```python
import requests
try:
    response = requests.get("http://localhost:9000/", timeout=2)
    print(f"✅ Server is running (Status: {response.status_code})")
except Exception as e:
    print(f"❌ Server is NOT running: {e}")
    print("Please start the server first!")
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

