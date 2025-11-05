"""Initialize database tables for local/Colab environment."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import Base
from app.dependencies import engine
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def init_database():
    """Create all database tables."""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info("Database tables created successfully", tables=tables)
        
        # Show table details
        for table_name in tables:
            if table_name != 'alembic_version':
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                logger.info(f"Table '{table_name}' columns", columns=columns)
        
        return True
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        return False


if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n✅ Database initialized successfully!")
        print("   Tables: models, garments, tryon_jobs")
    else:
        print("\n❌ Database initialization failed")
        sys.exit(1)

