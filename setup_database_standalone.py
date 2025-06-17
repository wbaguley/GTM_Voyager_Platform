"""
Standalone database setup script to avoid import issues
"""
import os
import sys
from pathlib import Path

# Set up environment
os.environ.setdefault("DATABASE_URL", "postgresql://gtm_admin:your_password@localhost:5432/gtm_voyager")

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    # Import SQLAlchemy directly
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    
    print("Testing basic database connection...")
    
    # Test connection
    engine = create_engine("postgresql://gtm_admin:gtm_secure_password_123@localhost:5432/gtm_voyager")
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
    
    print("Database setup completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure PostgreSQL is running and the database exists.")
    print("You may need to:")
    print("1. Start Docker: docker-compose up -d postgres")
    print("2. Create the database manually")

input("Press Enter to continue...")
