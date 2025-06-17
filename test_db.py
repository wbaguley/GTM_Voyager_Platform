from src.gtm_voyager.database.config import get_session_context
from src.gtm_voyager.database.models import User

with get_session_context() as session:
    users = session.query(User).all()
    print(f"Total users in database: {len(users)}")
    
    for user in users:
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"Status: {user.status}")
        print(f"Email verified: {user.is_email_verified}")
        print(f"Password hash exists: {bool(user.password_hash)}")
        print("---")
    
    # Try to find admin user specifically
    admin = session.query(User).filter_by(email="admin@gtmvoyager.com").first()
    print(f"Admin user found: {admin is not None}")
