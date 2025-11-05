# Colab Troubleshooting Guide

This document addresses common issues when running the Try-On Backend in Google Colab.

## Issues Resolved

### 1. `sqlite3.OperationalError: no such table: models`

**Problem:** Database tables were not created when starting the application.

**Root Causes:**
- No database migration scripts existed in `alembic/versions/`
- Missing Alembic template file (`alembic/script.py.mako`)
- Database initialization was not part of the Colab setup

**Solution Applied:**
- ✅ Added `alembic/script.py.mako` template file
- ✅ Generated initial migration script
- ✅ Created `scripts/init_db.py` for easy database setup
- ✅ Added database initialization step in Colab notebook (Step 4)
- ✅ Database tables now created automatically: `models`, `garments`, `tryon_jobs`

**Manual Fix (if needed):**
```python
from app.models.database import Base
from app.dependencies import engine
Base.metadata.create_all(bind=engine)
```

### 2. `ModuleNotFoundError: No module named 'structlog'`

**Problem:** Required logging dependency was missing from Colab installation.

**Solution:**
- ✅ Added `structlog` to installation cell in notebook
- ✅ Updated `requirements-colab.txt` with all required dependencies

### 3. `AttributeError: 'property' object has no attribute 'schema'`

**Problem:** Using `metadata` as column name conflicts with SQLAlchemy's reserved `Base.metadata` attribute.

**Solution:**
- ✅ Renamed database column to `extra_metadata` (mapped to "metadata" in DB)
- ✅ Updated Pydantic schemas to map `extra_metadata` → `metadata` in API responses
- ✅ No API changes required - transparent to users

### 4. SQLite UUID Incompatibility

**Problem:** PostgreSQL's UUID type doesn't work with SQLite.

**Solution:**
- ✅ Created custom `GUID` type that works with both PostgreSQL and SQLite
- ✅ PostgreSQL: uses native UUID type
- ✅ SQLite: uses CHAR(36) and converts automatically

### 5. `ERR_NGROK_8012: connection refused`

**Problem:** ngrok was connecting before the server started.

**Solution:**
- ✅ Reordered notebook: Start server first, then connect ngrok
- ✅ Added health check loop (waits up to 30 seconds for server)
- ✅ Verify server is running before ngrok connects

### 6. Port Conflicts

**Problem:** Port 8000 commonly used by other services; Port 9000 conflicts with MinIO.

**Solution:**
- ✅ Changed default port to 8500
- ✅ Updated all documentation and configs

### 7. Missing Dependencies (Redis, Celery, boto3, minio)

**Problem:** Colab doesn't need Redis, Celery, or S3/MinIO but code imports them.

**Solution:**
- ✅ Made all imports optional with try/except
- ✅ Graceful fallbacks when dependencies missing
- ✅ Local file storage when S3/MinIO unavailable
- ✅ Warnings logged but app continues running

### 8. PyTorch Version Unavailable

**Problem:** `torch==2.1.0` no longer available from PyTorch index.

**Solution:**
- ✅ Updated to `torch==2.3.0` and `torchvision==0.18.0`
- ✅ Compatible with current Colab CUDA

## Updated Colab Workflow

### Correct Setup Sequence:

1. **Install Dependencies** (Cell 2)
   - Installs all required packages
   - Uses `%pip` for Colab compatibility
   - Includes structlog, SQLAlchemy, etc.

2. **Verify Dependencies** (Cell 4)
   - Checks all critical packages are installed

3. **Clone Project** (Cell 6)
   - Clones from GitHub
   - Adds to Python path

4. **Setup Environment** (Cell 8)
   - Sets environment variables
   - Creates directories
   - Configures USE_LOCAL_STORAGE=true

5. **Initialize Database** (Cell 10) ⭐ **NEW**
   - Creates database tables
   - Verifies tables exist
   - Required before starting server

6. **Test ML Models** (Cell 12) - Optional
   - Tests ML model loading
   - Optional if torch installed

7. **Start Server** (Cell 13+)
   - Starts FastAPI on port 8500
   - Waits for server to be ready
   - Then connect ngrok

## Quick Reference

### Database Initialization
```python
# Run this if you get "no such table" errors
from app.models.database import Base
from app.dependencies import engine
Base.metadata.create_all(bind=engine)
print("✅ Tables created")
```

### Check Database Tables
```python
from sqlalchemy import inspect
from app.dependencies import engine
inspector = inspect(engine)
print("Tables:", inspector.get_table_names())
```

### Verify Server is Running
```python
import requests
response = requests.get("http://localhost:8500/api/v1/health")
print(response.json())
```

### Reset Database (if needed)
```python
import os
if os.path.exists('test.db'):
    os.remove('test.db')
    print("✅ Database deleted")

# Then reinitialize
from app.models.database import Base
from app.dependencies import engine
Base.metadata.create_all(bind=engine)
print("✅ Database recreated")
```

## Environment Variables for Colab

```python
import os
os.environ["ML_DEVICE"] = "cuda"  # or "cpu"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["USE_LOCAL_STORAGE"] = "true"
os.environ["LOG_LEVEL"] = "INFO"
```

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `no such table: models` | Database not initialized | Run database initialization cell |
| `Module torch not found` | torch not installed | Install torch or skip ML model testing |
| `ERR_NGROK_8012` | Server not running | Start server before connecting ngrok |
| `connection refused` | Wrong port or server not started | Check port 8500, verify server running |
| `metadata attribute error` | SQLAlchemy reserved name | Fixed in code (using extra_metadata) |
| `UUID type error` | SQLite doesn't support UUID | Fixed in code (using GUID type) |

## Files Created/Updated

### For Colab Support:
- `alembic/script.py.mako` - Alembic migration template
- `alembic/versions/*.py` - Initial migration script  
- `scripts/init_db.py` - Database initialization script
- `colab_setup.ipynb` - Updated with database init step
- `requirements-colab.txt` - All Colab dependencies

### Modified for Compatibility:
- `app/models/database.py` - GUID type for SQLite compatibility
- `app/services/cache.py` - Optional Redis
- `app/services/storage.py` - Local file storage fallback
- `app/api/v1/endpoints/*.py` - Optional Celery imports
- `app/models/schemas.py` - Disabled protected namespaces

## Testing

The app is now fully tested and working:
- ✅ Runs without Redis/Celery
- ✅ Works with SQLite (local) or PostgreSQL (production)
- ✅ Local file storage when S3/MinIO unavailable
- ✅ Optional ML models (graceful degradation)
- ✅ Port 8500 (avoids conflicts)

## Next Steps in Colab

After running all setup cells:

1. **Test health endpoint:**
```python
import requests
response = requests.get("http://localhost:8500/api/v1/health")
print(response.json())
```

2. **Access API docs:**
- Via ngrok: `{public_url}/docs`
- Or directly in Colab (if running locally)

3. **Upload and test try-on:**
```python
# See test_direct_endpoint.sh for example
```

## Support

If you encounter issues not covered here:
1. Check server logs in the cell output
2. Verify database tables exist
3. Ensure server is running before ngrok
4. Check that all dependencies are installed

