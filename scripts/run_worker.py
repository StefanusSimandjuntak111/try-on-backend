"""Script to run Celery worker."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workers.celery_app import celery_app

if __name__ == "__main__":
    celery_app.start()

