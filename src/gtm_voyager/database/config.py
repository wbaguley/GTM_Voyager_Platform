"""
GTM Voyager Platform - Database Configuration
Database connection, session management, and configuration utilities.
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "postgresql://gtm_admin:hRZTvBn8daL0TL@localhost:5432/gtm_voyager"
        )
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"

# Global database configuration
db_config = DatabaseConfig()

# Create database engine
engine = create_engine(
    db_config.database_url,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_timeout=db_config.pool_timeout,
    pool_recycle=db_config.pool_recycle,
    echo=db_config.echo
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database_url() -> str:
    """Get database URL"""
    return db_config.database_url

def create_engine_instance() -> Engine:
    """Create database engine instance"""
    return engine

def get_session() -> Generator[Session, None, None]:
    """
    Get database session for FastAPI dependency injection.
    Use this in FastAPI route dependencies.
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
