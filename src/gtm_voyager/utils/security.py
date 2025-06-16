import hashlib
import secrets
import logging
from typing import Dict, Any, Optional

class SecurityManager:
    """Security manager for GTM Voyager Platform."""
    
    def __init__(self, secret_key: str = None):
        """Initialize the security manager."""
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for SecurityManager operations."""
        logger = logging.getLogger('SecurityManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def hash_password(self, password: str) -> str:
        """Hash a password using SHA-256 with salt."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            salt, stored_hash = hashed_password.split(':')
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return password_hash == stored_hash
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False
    
    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    
    def sanitize_input(self, input_string: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Basic sanitization - remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
        sanitized = input_string
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()
