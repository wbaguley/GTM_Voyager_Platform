"""
GTM Voyager Platform - Database Initialization Script
Script to initialize database, create tables, and set up default data.
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.gtm_voyager.database.config import test_connection, get_connection_info
from src.gtm_voyager.database.migrations import (
    init_database, create_default_data, reset_database, upgrade_database
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main database initialization function"""
    print("=" * 60)
    print("GTM Voyager Platform - Database Initialization")
    print("=" * 60)
    
    # Check database connection
    print("\n1. Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed!")
        print("\nConnection info:")
        conn_info = get_connection_info()
        for key, value in conn_info.items():
            print(f"  {key}: {value}")
        print("\nPlease check your database configuration and try again.")
        return False
    
    print("✅ Database connection successful!")
    
    # Get user choice
    print("\nChoose an option:")
    print("1. Initialize database (create tables only)")
    print("2. Initialize database with default data")
    print("3. Reset database (WARNING: This will delete all data!)")
    print("4. Upgrade database schema")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                print("\n2. Initializing database tables...")
                if init_database():
                    print("✅ Database tables created successfully!")
                    return True
                else:
                    print("❌ Database initialization failed!")
                    return False
            
            elif choice == "2":
                print("\n2. Initializing database with default data...")
                if init_database():
                    print("✅ Database tables created successfully!")
                    
                    print("\n3. Creating default data...")
                    if create_default_data(include_demo=True):
                        print("✅ Default data created successfully!")
                        print("\n🔐 Default Admin Credentials:")
                        print("   Email: admin@gtmvoyager.com")
                        print("   Password: GTMVoyager2024!")
                        print("   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
                        return True
                    else:
                        print("❌ Default data creation failed!")
                        return False
                else:
                    print("❌ Database initialization failed!")
                    return False
            
            elif choice == "3":
                print("\n⚠️  WARNING: This will delete ALL existing data!")
                confirm = input("Type 'RESET' to confirm: ").strip()
                
                if confirm == "RESET":
                    print("\n2. Resetting database...")
                    if reset_database(include_demo=True):
                        print("✅ Database reset successfully!")
                        print("\n🔐 Default Admin Credentials:")
                        print("   Email: admin@gtmvoyager.com")
                        print("   Password: GTMVoyager2024!")
                        print("   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
                        return True
                    else:
                        print("❌ Database reset failed!")
                        return False
                else:
                    print("Reset cancelled.")
                    continue
            
            elif choice == "4":
                print("\n2. Upgrading database schema...")
                if upgrade_database():
                    print("✅ Database upgrade completed successfully!")
                    return True
                else:
                    print("❌ Database upgrade failed!")
                    return False
            
            elif choice == "5":
                print("Exiting...")
                return True
            
            else:
                print("Invalid choice. Please enter 1-5.")
                continue
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            return False
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
