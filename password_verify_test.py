"""
Test password verification
"""
import sys
sys.path.append('src')

try:
    from gtm_voyager.utils.security import SecurityManager
    from gtm_voyager.database.config import get_session_context
    from gtm_voyager.database.models import User
    
    security = SecurityManager()
    
    with get_session_context() as db:
        # Test demo user
        user = db.query(User).filter(User.email.ilike("demo@dental.com")).first()
        if user:
            print(f"Testing password for user: {user.email}")
            print(f"Password hash: {user.password_hash[:50]}...")
            
            # Test correct password
            ok = security.verify_password("demo123", user.password_hash)
            print(f"Password 'demo123' valid: {ok}")
            
            # Test wrong password
            wrong = security.verify_password("wrongpassword", user.password_hash)
            print(f"Wrong password valid: {wrong}")
            
        else:
            print("❌ Demo user not found")
            
        # Test admin user
        admin = db.query(User).filter(User.email.ilike("admin@gtmvoyager.com")).first()
        if admin:
            print(f"\nTesting password for admin: {admin.email}")
            print(f"Password hash: {admin.password_hash[:50]}...")
            
            # Test correct password
            ok_admin = security.verify_password("GTMVoyager2024!", admin.password_hash)
            print(f"Password 'GTMVoyager2024!' valid: {ok_admin}")
            
        else:
            print("❌ Admin user not found")
            
except Exception as e:
    print(f"❌ Password verification test failed: {e}")
    import traceback
    traceback.print_exc()
