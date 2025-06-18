"""
Generate fresh password hashes and update database
"""
import sys
sys.path.append('src')

from gtm_voyager.utils.security import SecurityManager
from gtm_voyager.database.config import get_session_context
from gtm_voyager.database.models import User

security = SecurityManager()

# Generate fresh hashes
demo_hash = security.hash_password("demo123")
admin_hash = security.hash_password("GTMVoyager2024!")

print(f"Demo hash length: {len(demo_hash)}")
print(f"Admin hash length: {len(admin_hash)}")
print(f"Demo hash: {demo_hash}")
print(f"Admin hash: {admin_hash}")

# Update database
with get_session_context() as db:
    # Update demo user
    demo_user = db.query(User).filter(User.email.ilike("demo@dental.com")).first()
    if demo_user:
        demo_user.password_hash = demo_hash
        print("✅ Updated demo user password hash")
    
    # Update admin user
    admin_user = db.query(User).filter(User.email.ilike("admin@gtmvoyager.com")).first()
    if admin_user:
        admin_user.password_hash = admin_hash
        print("✅ Updated admin user password hash")
    
    db.commit()
    print("✅ Database updated successfully")
