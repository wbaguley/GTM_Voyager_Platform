"""
Test the actual authentication endpoint logic
"""
import sys
sys.path.append('src')

from gtm_voyager.database.config import get_session_context
from gtm_voyager.database.models import User
from gtm_voyager.utils.security import SecurityManager

# Test the exact same logic the auth endpoint uses
def test_login_logic(email: str, password: str):
    print(f"Testing login for: {email}")
    
    with get_session_context() as db:
        # Find user (same as auth endpoint)
        user = db.query(User).filter(User.email.ilike(email)).first()
        
        if not user:
            print("❌ User not found")
            return False
            
        print(f"✅ User found: {user.email}")
        print(f"User status: {user.status}")
        print(f"Email verified: {user.is_email_verified}")
        
        # Check password (same as auth endpoint)
        security = SecurityManager()
        password_valid = security.verify_password(password, user.password_hash)
        print(f"Password valid: {password_valid}")
        
        # Check if account is active
        if user.status != "active":
            print(f"❌ Account not active. Status: {user.status}")
            return False
            
        if not user.is_email_verified:
            print("❌ Email not verified")
            return False
            
        return password_valid

# Test both users
print("=== Testing Demo User ===")
demo_result = test_login_logic("demo@dental.com", "demo123")
print(f"Demo login result: {demo_result}")

print("\n=== Testing Admin User ===")
admin_result = test_login_logic("admin@gtmvoyager.com", "GTMVoyager2024!")
print(f"Admin login result: {admin_result}")
