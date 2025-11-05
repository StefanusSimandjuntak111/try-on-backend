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
git clone <repository-url>
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

6. Run the application:
```bash
uvicorn app.main:app --reload
```

### Docker Setup

```bash
docker-compose up --build
```

## 📚 API Documentation

Once the server is running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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

