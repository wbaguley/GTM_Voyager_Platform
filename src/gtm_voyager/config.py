"""
GTM Voyager Platform - Database Configuration
Database connection, session management, and configuration utilities.
"""

import os
import logging
from typing import Generator, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.echo = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        self.pool_size = int(os.getenv("DATABASE_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        # Try the full DATABASE_URL first
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            return database_url
        
        # Build from individual components
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "gtm_voyager")
        db_user = os.getenv("DB_USER", "gtm_admin")
        db_password = os.getenv("DB_PASSWORD", "")
        
        if not db_password:
            # Try alternative environment variable names
            db_password = os.getenv("POSTGRES_PASSWORD", "")
        
        if not db_password:
            raise ValueError("Database password not found in environment variables")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Global database configuration
db_config = DatabaseConfig()

def get_database_url() -> str:
    """Get the database URL"""
    return db_config.database_url

def create_engine() -> Engine:
    """Create SQLAlchemy engine with connection pooling"""
    engine = create_engine(
        db_config.database_url,
        echo=db_config.echo,
        poolclass=QueuePool,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_timeout=db_config.pool_timeout,
        pool_recycle=db_config.pool_recycle,
        pool_pre_ping=True,  # Verify connections before use
        connect_args={
            "options": "-c timezone=utc",
            "application_name": "gtm_voyager_platform"
        }
    )
    
    logger.info(f"Database engine created with pool_size={db_config.pool_size}")
    return engine

# Create global engine and session factory
engine = create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session() -> Generator[Session, None, None]:
    """
    Get database session with automatic cleanup.
    Use this as a dependency in FastAPI routes.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

@contextmanager
def get_session_context():
    """
    Get database session as context manager.
    Use this for non-FastAPI database operations.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_session_context() as session:
            session.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def get_connection_info() -> dict:
    """Get database connection information for debugging"""
    return {
        "database_url": db_config.database_url.replace(
            db_config.database_url.split("://")[1].split("@")[0], "***:***"
        ),  # Hide credentials
        "pool_size": db_config.pool_size,
        "max_overflow": db_config.max_overflow,
        "pool_timeout": db_config.pool_timeout,
        "pool_recycle": db_config.pool_recycle,
        "echo": db_config.echo
    }
