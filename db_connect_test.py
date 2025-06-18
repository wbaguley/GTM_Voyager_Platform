"""
Test database connection
"""
import sys
import os
sys.path.append('src')

try:
    from gtm_voyager.database.config import engine
    import sqlalchemy as sa
    
    with engine.connect() as conn:
        result = conn.execute(sa.text("SELECT 1"))
        print("✅ DB connection ok")
        print(f"Database URL: {os.getenv('DATABASE_URL', 'Using default from config')}")
except Exception as e:
    print(f"❌ DB connection failed: {e}")
    import traceback
    traceback.print_exc()
