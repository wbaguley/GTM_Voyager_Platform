"""
GTM Voyager Platform - Enhanced Security Manager
Enterprise-grade security utilities with bcrypt, input validation, and threat detection.
"""

import hashlib
import secrets
import logging
import re
import ipaddress
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import bcrypt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import os

logger = logging.getLogger(__name__)

class SecurityManager:
    """Enhanced security manager with enterprise-grade security features"""
    
    def __init__(self, secret_key: str = None):
        """Initialize the security manager with enhanced features"""
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        
        # Password hashing with bcrypt
        self.bcrypt_rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=self.bcrypt_rounds
        )
        
        # Encryption for sensitive data
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Rate limiting and security thresholds
        self.rate_limit_window = 300  # 5 minutes
        self.max_requests_per_window = 100
        self.suspicious_activity_threshold = 10
        
        # Request tracking for rate limiting
        self.request_tracking = {}
        self.failed_attempts = {}
        
        self.logger = self._setup_logger()
        self.logger.info("Enhanced Security Manager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for SecurityManager operations"""
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
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for sensitive data"""
        key_env = os.getenv("ENCRYPTION_KEY")
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env)
            except Exception:
                self.logger.warning("Invalid encryption key in environment, generating new one")
        
        # Generate new key
        key = Fernet.generate_key()
        self.logger.warning(f"Generated new encryption key: {base64.urlsafe_b64encode(key).decode()}")
        self.logger.warning("Store this key in ENCRYPTION_KEY environment variable for production!")
        return key
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt with configurable rounds"""
        try:
            return self.pwd_context.hash(password)
        except Exception as e:
            self.logger.error(f"Password hashing failed: {e}")
            raise
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return self.pwd_context.verify(password, hashed_password)
        except Exception as e:
            self.logger.error(f"Password verification failed: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength according to security policy.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Length check
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            issues.append("Password must be less than 128 characters long")
        
        # Character requirements
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one digit")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        # Common password patterns
        common_patterns = [
            r'123456', r'password', r'qwerty', r'abc123', r'admin',
            r'letmein', r'welcome', r'monkey', r'dragon'
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                issues.append("Password contains common patterns and is not secure")
                break
        
        # Sequential characters
        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):
            issues.append("Password contains sequential numbers")
        
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            issues.append("Password contains sequential letters")
        
        return len(issues) == 0, issues
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate a cryptographically secure password"""
        if length < 8:
            length = 8
        if length > 128:
            length = 128
        
        # Character sets
        lowercase = 'abcdefghijklmnopqrstuvwxyz'
        uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        digits = '0123456789'
        special = '!@#$%^&*(),.?":{}|<>'
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill remaining length with random characters
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)
    
    def generate_api_key(self, prefix: str = "gtm") -> Tuple[str, str]:
        """
        Generate a secure API key with prefix.
        
        Returns:
            Tuple of (full_api_key, key_hash_for_storage)
        """
        # Generate random part
        random_part = secrets.token_urlsafe(32)
        
        # Create full API key
        api_key = f"{prefix}_{random_part}"
        
        # Create hash for storage
        key_hash = self.hash_api_key(api_key)
        
        return api_key, key_hash
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        """Verify API key against stored hash"""
        return self.hash_api_key(api_key) == stored_hash
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            self.logger.error(f"Data encryption failed: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data from storage"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            self.logger.error(f"Data decryption failed: {e}")
            raise
    
    def sanitize_input(self, input_string: str, max_length: int = 1000) -> str:
        """Enhanced input sanitization to prevent injection attacks"""
        if not isinstance(input_string, str):
            return ""
        
        # Truncate if too long
        if len(input_string) > max_length:
            input_string = input_string[:max_length]
        
        # Remove null bytes
        sanitized = input_string.replace('\x00', '')
        
        # Remove or escape dangerous characters for SQL injection
        dangerous_sql = ['--', ';--', '/*', '*/', 'xp_', 'sp_', 'EXEC', 'EXECUTE']
        for pattern in dangerous_sql:
            sanitized = sanitized.replace(pattern, '')
        
        # Remove or escape dangerous characters for XSS
        xss_patterns = {
            '<script': '&lt;script',
            '</script>': '&lt;/script&gt;',
            'javascript:': 'javascript&#58;',
            'vbscript:': 'vbscript&#58;',
            'onload=': 'onload&#61;',
            'onerror=': 'onerror&#61;',
            'onclick=': 'onclick&#61;'
        }
        
        for pattern, replacement in xss_patterns.items():
            sanitized = sanitized.replace(pattern, replacement)
            sanitized = sanitized.replace(pattern.upper(), replacement)
        
        # Remove control characters except newline and tab
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t')
        
        return sanitized.strip()
    
    def validate_email(self, email: str) -> bool:
        """Validate email address format"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email)) and len(email) <= 255
    
    def validate_ip_address(self, ip: str) -> bool:
        """Validate IP address (IPv4 or IPv6)"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def is_private_ip(self, ip: str) -> bool:
        """Check if IP address is private/internal"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False
    
    def check_rate_limit(self, identifier: str, max_requests: int = None, 
                        window_seconds: int = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if identifier (IP, user, etc.) is within rate limits.
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        max_requests = max_requests or self.max_requests_per_window
        window_seconds = window_seconds or self.rate_limit_window
        
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old entries
        if identifier in self.request_tracking:
            self.request_tracking[identifier] = [
                timestamp for timestamp in self.request_tracking[identifier]
                if timestamp > window_start
            ]
        else:
            self.request_tracking[identifier] = []
        
        # Check current count
        current_count = len(self.request_tracking[identifier])
        
        if current_count >= max_requests:
            # Rate limit exceeded
            oldest_request = min(self.request_tracking[identifier])
            reset_time = oldest_request + timedelta(seconds=window_seconds)
            
            return False, {
                "allowed": False,
                "current_count": current_count,
                "max_requests": max_requests,
                "window_seconds": window_seconds,
                "reset_time": reset_time.isoformat(),
                "retry_after": int((reset_time - now).total_seconds())
            }
        
        # Add current request
        self.request_tracking[identifier].append(now)
        
        return True, {
            "allowed": True,
            "current_count": current_count + 1,
            "max_requests": max_requests,
            "window_seconds": window_seconds,
            "remaining": max_requests - current_count - 1
        }
    
    def detect_suspicious_activity(self, identifier: str, activity_type: str) -> Dict[str, Any]:
        """
        Detect suspicious activity patterns.
        
        Returns:
            Dictionary with risk assessment and recommendations
        """
        now = datetime.utcnow()
        risk_score = 0
        flags = []
        
        # Track failed attempts
        if activity_type in ['failed_login', 'invalid_token', 'unauthorized_access']:
            if identifier not in self.failed_attempts:
                self.failed_attempts[identifier] = []
            
            # Clean old attempts (last hour)
            hour_ago = now - timedelta(hours=1)
            self.failed_attempts[identifier] = [
                timestamp for timestamp in self.failed_attempts[identifier]
                if timestamp > hour_ago
            ]
            
            # Add current attempt
            self.failed_attempts[identifier].append(now)
            
            # Analyze patterns
            recent_failures = len(self.failed_attempts[identifier])
            
            if recent_failures >= 10:
                risk_score += 80
                flags.append("high_failure_rate")
            elif recent_failures >= 5:
                risk_score += 50
                flags.append("moderate_failure_rate")
            elif recent_failures >= 3:
                risk_score += 20
                flags.append("elevated_failure_rate")
        
        # Check rate limiting
        is_allowed, rate_info = self.check_rate_limit(identifier)
        if not is_allowed:
            risk_score += 30
            flags.append("rate_limit_exceeded")
        
        # Time-based analysis
        hour = now.hour
        if hour < 6 or hour > 22:  # Outside normal business hours
            risk_score += 10
            flags.append("off_hours_activity")
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        elif risk_score >= 10:
            risk_level = "low"
        else:
            risk_level = "minimal"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "flags": flags,
            "recommendations": self._get_security_recommendations(risk_level, flags),
            "timestamp": now.isoformat()
        }
    
    def _get_security_recommendations(self, risk_level: str, flags: List[str]) -> List[str]:
        """Get security recommendations based on risk assessment"""
        recommendations = []
        
        if "high_failure_rate" in flags:
            recommendations.append("Temporarily block IP address")
            recommendations.append("Require additional authentication")
            recommendations.append("Alert security team")
        
        if "rate_limit_exceeded" in flags:
            recommendations.append("Implement progressive delays")
            recommendations.append("Monitor for DDoS patterns")
        
        if "off_hours_activity" in flags:
            recommendations.append("Require additional verification")
            recommendations.append("Log for security review")
        
        if risk_level in ["high", "critical"]:
            recommendations.append("Escalate to security team")
            recommendations.append("Consider account lockout")
            recommendations.append("Enable enhanced monitoring")
        
        return recommendations
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for form protection"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        data = f"{session_id}:{timestamp}:{self.secret_key}"
        token = hashlib.sha256(data.encode()).hexdigest()
        return f"{timestamp}.{token}"
    
    def validate_csrf_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """Validate CSRF token"""
        try:
            timestamp_str, token_hash = token.split('.', 1)
            timestamp = int(timestamp_str)
            
            # Check age
            now = int(datetime.utcnow().timestamp())
            if now - timestamp > max_age:
                return False
            
            # Verify token
            expected_data = f"{session_id}:{timestamp_str}:{self.secret_key}"
            expected_hash = hashlib.sha256(expected_data.encode()).hexdigest()
            
            return token_hash == expected_hash
            
        except (ValueError, AttributeError):
            return False
    
    def secure_compare(self, a: str, b: str) -> bool:
        """Constant-time string comparison to prevent timing attacks"""
        if len(a) != len(b):
            return False
        
        result = 0
        for x, y in zip(a, b):
            result |= ord(x) ^ ord(y)
        
        return result == 0
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get recommended security headers for HTTP responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

# Global security manager instance
security_manager = SecurityManager()
