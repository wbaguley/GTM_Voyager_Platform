"""
Test user lookup - checking for case sensitivity issues
"""
import sys
sys.path.append('src')

try:
    from gtm_voyager.database.config import get_session_context
    from gtm_voyager.database.models import User
    
    email = "demo@dental.com"
    
    with get_session_context() as db:
        # Test exact case match
        user_exact = db.query(User).filter(User.email == email).first()
        print(f"Exact case match for '{email}': {bool(user_exact)}")
        
        # Test case-insensitive match
        user_ilike = db.query(User).filter(User.email.ilike(email)).first()
        print(f"Case-insensitive match for '{email}': {bool(user_ilike)}")
        
        # Test with different cases
        email_upper = email.upper()
        user_upper = db.query(User).filter(User.email == email_upper).first()
        print(f"Uppercase match for '{email_upper}': {bool(user_upper)}")
        
        # Show all users in database
        all_users = db.query(User).all()
        print(f"\nAll users in database:")
        for user in all_users:
            print(f"  - {user.email} (status: {user.status})")
            
        # If we found a user, show details
        if user_ilike:
            print(f"\nUser details:")
            print(f"  Email: {user_ilike.email}")
            print(f"  Username: {user_ilike.username}")
            print(f"  Status: {user_ilike.status}")
            print(f"  Email verified: {user_ilike.is_email_verified}")
            print(f"  2FA enabled: {user_ilike.is_2fa_enabled}")
            print(f"  Locked until: {user_ilike.locked_until}")
            print(f"  Failed attempts: {user_ilike.failed_login_attempts}")
            
except Exception as e:
    print(f"❌ User lookup test failed: {e}")
    import traceback
    traceback.print_exc()
