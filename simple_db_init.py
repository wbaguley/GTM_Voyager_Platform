"""
Simple database initialization script
"""
import os
import sys
from pathlib import Path

# Add project to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Set environment variables
os.environ.setdefault("DATABASE_URL", "postgresql://gtm_admin:hRZTvBn8daL0TL@localhost:5432/gtm_voyager")

try:
    from sqlalchemy import create_engine, text, Column, Integer, String, Boolean, DateTime, Text
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from datetime import datetime
    import uuid
    
    print("Creating database connection...")
    
    # Create engine and session
    engine = create_engine("postgresql://gtm_admin:hRZTvBn8daL0TL@localhost:5432/gtm_voyager")
    SessionLocal = sessionmaker(bind=engine)
    Base = declarative_base()
    
    # Simple User table for testing
    class User(Base):
        __tablename__ = "users"
        
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        email = Column(String(255), unique=True, nullable=False)
        password_hash = Column(String(255), nullable=False)
        full_name = Column(String(255), nullable=False)
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)
    
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    print("✅ Authentication system initialized!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

input("Press Enter to continue...")
