# AI Try-On Backend

A FastAPI-based backend for AI-powered virtual try-on system that generates realistic try-on results using deep learning models.

## 🚀 Features

- **RESTful API** for model and garment management
- **Async Processing** using Celery workers
- **ML Model Integration**: HR-VITON, SCHP, OpenPose, U2-Net
- **Object Storage** support (S3/MinIO)
- **PostgreSQL** database for metadata
- **Redis** caching and task queue
- **Docker** containerization

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)
- CUDA-capable GPU (recommended for production)

## 🛠️ Installation

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/StefanusSimandjuntak111/try-on-backend.git
cd try-on-backend
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Setup environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
alembic upgrade head
```

6. Download model weights (optional):
```bash
# Install gdown for Google Drive downloads
pip install gdown

# Download weights
python scripts/download_weights.py --show-instructions
```
See [WEIGHTS_DOWNLOAD.md](WEIGHTS_DOWNLOAD.md) for detailed instructions.

7. Run the application:
```bash
uvicorn app.main:app --reload
```

### Docker Setup

1. Copy environment file:
```bash
cp .env.example .env
# Edit .env with your configuration if needed
```

2. Start all services:
```bash
docker-compose up --build
```

3. The application will be available at:
   - API: http://localhost:8500
   - API Docs: http://localhost:8500/docs
   - MinIO Console: http://localhost:9001 (default: minioadmin/minioadmin)

4. Services included:
   - **api**: FastAPI application
   - **postgres**: PostgreSQL database
   - **redis**: Redis cache and message broker
   - **minio**: S3-compatible object storage
   - **celery-preprocessing**: Worker for image preprocessing
   - **celery-inference**: Worker for ML inference
   - **celery-maintenance**: Worker for maintenance tasks
   - **celery-beat**: Task scheduler

5. To run in detached mode:
```bash
docker-compose up -d --build
```

6. To view logs:
```bash
docker-compose logs -f [service-name]
```

7. To stop services:
```bash
docker-compose down
```

8. To remove volumes (clean data):
```bash
docker-compose down -v
```

## 📚 API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8500/docs
- ReDoc: http://localhost:8500/redoc

For detailed API usage and examples, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

### Quick Start - Try-On API

**Direct upload (recommended):**
```bash
curl -X POST "http://localhost:8500/api/v1/tryon/direct" \
  -F "model_file=@person.jpg" \
  -F "garment_file=@clothing.jpg"
```

**Get result:**
```bash
curl "http://localhost:8500/api/v1/tryon/{job_id}"
```

The response contains `result_url` which points to the final fitted image (clothing on model).

## 🏗️ Project Structure

```
try-on-backend/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Core utilities
│   ├── models/       # Database models & schemas
│   ├── services/     # Business logic
│   ├── workers/      # Celery tasks
│   └── ml/           # ML model integrations
├── tests/            # Test suite
├── scripts/          # Utility scripts
└── alembic/          # Database migrations
```

## 🧪 Testing

```bash
pytest tests/
```

## 📝 License

MIT License

