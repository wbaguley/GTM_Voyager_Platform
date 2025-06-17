"""
GTM Voyager Platform - Authentication Tests
Comprehensive tests for the authentication system.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from src.gtm_voyager.api.main import app
from src.gtm_voyager.database.models import Base, User, Role, Permission
from src.gtm_voyager.database.config import get_session
from src.gtm_voyager.database.migrations import create_default_data
from src.gtm_voyager.api.auth import auth_manager
from src.gtm_voyager.utils.security import security_manager

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} )
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_session():
    """Override database session for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(scope="module")
def setup_test_db():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    with TestingSessionLocal() as session:
        # Create a test user
        test_user = User(
            email="test@example.com",
            username="testuser",
            password_hash=security_manager.hash_password("TestPassword123!"),
            first_name="Test",
            last_name="User",
            status="active",
            is_email_verified=True,
            tenant_id="test_tenant"
        )
        session.add(test_user)
        session.commit()
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_auth.db"):
        os.remove("./test_auth.db")

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

class TestAuthentication:
    """Test authentication functionality"""
    
    def test_login_success(self, client, setup_test_db):
        """Test successful login"""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_invalid_credentials(self, client, setup_test_db):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client, setup_test_db):
        """Test login with nonexistent user"""
        response = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password"
        })
        
        assert response.status_code == 401
    
    def test_protected_route_without_token(self, client, setup_test_db):
        """Test accessing protected route without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_protected_route_with_token(self, client, setup_test_db):
        """Test accessing protected route with valid token"""
        # Login first
        login_response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        token = login_response.json()["access_token"]
        
        # Access protected route
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    
    def test_token_refresh(self, client, setup_test_db):
        """Test token refresh functionality"""
        # Login first
        login_response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh token
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_logout(self, client, setup_test_db):
        """Test logout functionality"""
        # Login first
        login_response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "TestPassword123!"
        })
        
        token = login_response.json()["access_token"]
        
        # Logout
        response = client.post("/auth/logout", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200

class TestPasswordSecurity:
    """Test password security features"""
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        # Weak passwords
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "short",
            "NoNumbers!",
            "nonumbers123",
            "NOLOWERCASE123!",
            "NoSpecialChars123"
        ]
        
        for password in weak_passwords:
            is_valid, issues = security_manager.validate_password_strength(password)
            assert not is_valid
            assert len(issues) > 0
        
        # Strong password
        is_valid, issues = security_manager.validate_password_strength("StrongPassword123!")
        assert is_valid
        assert len(issues) == 0
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        
        # Hash password
        hashed = security_manager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long
        
        # Verify correct password
        assert security_manager.verify_password(password, hashed)
        
        # Verify incorrect password
        assert not security_manager.verify_password("wrongpassword", hashed)
    
    def test_secure_password_generation(self):
        """Test secure password generation"""
        password = security_manager.generate_secure_password(16)
        
        assert len(password) == 16
        
        # Check password strength
        is_valid, issues = security_manager.validate_password_strength(password)
        assert is_valid

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiting(self):
        """Test rate limiting mechanism"""
        identifier = "test_user"
        
        # Should allow requests within limit
        for i in range(5):
            is_allowed, info = security_manager.check_rate_limit(identifier, max_requests=10)
            assert is_allowed
        
        # Should block after limit exceeded
        for i in range(10):
            security_manager.check_rate_limit(identifier, max_requests=10)
        
        is_allowed, info = security_manager.check_rate_limit(identifier, max_requests=10)
        assert not is_allowed

class TestSecurityFeatures:
    """Test security features"""
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        dangerous_input = "<script>alert('xss')</script>SELECT * FROM users--"
        sanitized = security_manager.sanitize_input(dangerous_input)
        
        assert "<script>" not in sanitized
        assert "SELECT" not in sanitized
        assert "--" not in sanitized
    
    def test_api_key_generation(self):
        """Test API key generation and verification"""
        api_key, key_hash = security_manager.generate_api_key("test")
        
        assert api_key.startswith("test_")
        assert len(api_key) > 20
        
        # Verify API key
        assert security_manager.verify_api_key(api_key, key_hash)
        assert not security_manager.verify_api_key("wrong_key", key_hash)
    
    def test_data_encryption(self):
        """Test data encryption and decryption"""
        sensitive_data = "This is sensitive information"
        
        # Encrypt data
        encrypted = security_manager.encrypt_sensitive_data(sensitive_data)
        assert encrypted != sensitive_data
        
        # Decrypt data
        decrypted = security_manager.decrypt_sensitive_data(encrypted)
        assert decrypted == sensitive_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
