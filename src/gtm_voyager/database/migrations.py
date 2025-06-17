"""
GTM Voyager Platform - Database Migrations
Database initialization, schema creation, and default data setup.
"""

import logging
import uuid
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from .models import Base, User, Role, Permission
from .config import engine, get_session_context

logger = logging.getLogger(__name__)

def init_database(drop_existing: bool = False) -> bool:
    """Initialize database schema and create tables."""
    try:
        if drop_existing:
            Base.metadata.drop_all(bind=engine)
        
        # Enable UUID extension first
        with get_session_context() as session:
            session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            session.commit()
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def create_default_data(include_demo: bool = True) -> bool:
    """Create default permissions, roles, and users."""
    try:
        from ..utils.security import security_manager
        
        with get_session_context() as session:
            # Check if admin user already exists
            existing_admin = session.query(User).filter(User.email == "admin@gtmvoyager.com").first()
            if existing_admin:
                logger.info("Admin user already exists")
                return True
            
            # Create default admin user with correct field names
            admin_user = User(
                id=uuid.uuid4(),
                email="admin@gtmvoyager.com",
                username="admin",
                password_hash=security_manager.hash_password("GTMVoyager2024!"),
                first_name="System",
                last_name="Administrator",
                tenant_id="system",
                status="active",
                is_email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(admin_user)
            session.commit()
            
            logger.info("Default admin user created successfully")
            logger.info("Email: admin@gtmvoyager.com")
            logger.info("Username: admin")
            logger.info("Password: GTMVoyager2024!")
            logger.warning("CHANGE THIS PASSWORD IMMEDIATELY!")
            
            return True
            
    except Exception as e:
        logger.error(f"Default data creation failed: {e}")
        return False

def reset_database(include_demo: bool = True) -> bool:
    """Reset database by dropping and recreating all tables."""
    return init_database(drop_existing=True) and create_default_data(include_demo)

def upgrade_database() -> bool:
    """Upgrade database schema for new versions."""
    return init_database()
