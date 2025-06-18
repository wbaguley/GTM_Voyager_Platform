"""
GTM Voyager Platform - Enhanced Authentication Manager
JWT-based authentication with database integration, 2FA, and enterprise security.
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import jwt
import pyotp
import qrcode
from io import BytesIO
import base64
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database.models import User, UserSession, APIKey, AuditLog, SecurityEvent, UserStatus, SessionStatus
from ..database.config import get_session_context
from ..utils.security import SecurityManager

logger = logging.getLogger(__name__)

@dataclass
class AuthResult:
    """Authentication result with user info and tokens"""
    success: bool
    user: Optional[User] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    session_id: Optional[str] = None
    requires_2fa: bool = False
    error_message: Optional[str] = None
    risk_score: int = 0

@dataclass
class TokenPayload:
    """JWT token payload structure"""
    user_id: str
    session_id: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]
    exp: datetime
    iat: datetime
    type: str  # 'access' or 'refresh'

class EnhancedAuthManager:
    """Enhanced authentication manager with JWT, 2FA, and enterprise security"""
    
    def __init__(self):
        self.security_manager = SecurityManager()
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration_minutes = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
        
        # 2FA settings
        self.totp_issuer = os.getenv("TOTP_ISSUER", "GTM Voyager Platform")
        self.totp_digits = int(os.getenv("TOTP_DIGITS", "6"))
        self.totp_period = int(os.getenv("TOTP_PERIOD", "30"))
        
        logger.info("Enhanced Authentication Manager initialized")
    
    def authenticate_user(self, email: str, password: str, 
                         ip_address: str = None, user_agent: str = None,
                         totp_code: str = None) -> AuthResult:
        """
        Authenticate user with email/password and optional 2FA.
        
        Args:
            email: User email address
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent
            totp_code: TOTP code for 2FA (if enabled)
            
        Returns:
            AuthResult with authentication status and tokens
        """
        try:
              # DEBUG: Log the incoming request
            logger.info(f"DEBUG: Login attempt for email: {email}")
            with get_session_context() as session:
                # Find user by email
                user = session.query(User).filter_by(email=email.lower()).first()
                
                # DEBUG: Log user lookup result
                logger.info(f"DEBUG: User found: {user is not None}")
                if user:
                    logger.info(f"DEBUG: User email: {user.email}")
                    logger.info(f"DEBUG: User status: {user.status}")
                    logger.info(f"DEBUG: User is_locked: {user.is_locked}")
                else:
                    logger.info(f"DEBUG: No user found for email: {email.lower()}")
                
                if not user:
                    self._log_security_event(
                        session, "login_failed", "medium", "authentication",
                        ip_address, user_agent, None, 
                        {"reason": "user_not_found", "email": email}
                    )
                    return AuthResult(
                        success=False,
                        error_message="Invalid credentials",
                        risk_score=30
                    )
                
                # Check if account is locked
                if user.is_locked:
                    self._log_security_event(
                        session, "login_blocked", "high", "authentication",
                        ip_address, user_agent, user.id,
                        {"reason": "account_locked", "locked_until": user.locked_until.isoformat()}
                    )
                    return AuthResult(
                        success=False,
                        error_message="Account is temporarily locked",
                        risk_score=50
                    )
                
                # Check if account is active
                if user.status != UserStatus.ACTIVE.value:
                    self._log_security_event(
                        session, "login_blocked", "medium", "authentication",
                        ip_address, user_agent, user.id,
                        {"reason": "account_inactive", "status": user.status}
                    )
                    return AuthResult(
                        success=False,
                        error_message="Account is not active",
                        risk_score=40
                    )
                
                # Verify password
                if not self.security_manager.verify_password(password, user.password_hash):
                    # Increment failed login attempts
                    user.failed_login_attempts += 1
                    
                    # Lock account if too many failed attempts
                    if user.failed_login_attempts >= self.max_login_attempts:
                        user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
                        logger.warning(f"Account locked for user {user.email} due to failed login attempts")
                    
                    session.commit()
                    
                    self._log_security_event(
                        session, "login_failed", "medium", "authentication",
                        ip_address, user_agent, user.id,
                        {"reason": "invalid_password", "attempts": user.failed_login_attempts}
                    )
                    
                    return AuthResult(
                        success=False,
                        error_message="Invalid credentials",
                        risk_score=40
                    )
                
                # Check 2FA if enabled
                if user.is_2fa_enabled:
                    if not totp_code:
                        return AuthResult(
                            success=False,
                            requires_2fa=True,
                            error_message="2FA code required",
                            risk_score=10
                        )
                    
                    if not self._verify_totp(user.totp_secret, totp_code):
                        self._log_security_event(
                            session, "2fa_failed", "high", "authentication",
                            ip_address, user_agent, user.id,
                            {"reason": "invalid_totp_code"}
                        )
                        return AuthResult(
                            success=False,
                            error_message="Invalid 2FA code",
                            risk_score=60
                        )
                
                # Authentication successful - reset failed attempts
                user.failed_login_attempts = 0
                user.locked_until = None
                user.last_login = datetime.utcnow()
                
                # Create session
                session_result = self._create_user_session(
                    session, user, ip_address, user_agent
                )
                
                if not session_result:
                    return AuthResult(
                        success=False,
                        error_message="Failed to create session",
                        risk_score=20
                    )
                
                user_session, access_token, refresh_token = session_result
                
                # Log successful authentication
                self._log_audit_event(
                    session, user.id, "login", "authentication", "success",
                    ip_address, user_agent, user_session.session_token, user.tenant_id,
                    {"session_id": str(user_session.id)}
                )
                
                 # Create user data dict before committing to avoid session binding issues
                user_data = {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "tenant_id": user.tenant_id,
                    "status": user.status
                }
                session.commit()

                return AuthResult(
                    success=True,
                    user=user_data,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    session_id=str(user_session.id),
                    risk_score=0
                )
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return AuthResult(
                success=False,
                error_message="Authentication service error",
                risk_score=80
            )
    
    def _create_user_session(self, session: Session, user: User, 
                           ip_address: str = None, user_agent: str = None) -> Optional[Tuple[UserSession, str, str]]:
        """Create user session and generate JWT tokens"""
        try:
            # Create session record
            session_token = secrets.token_urlsafe(32)
            refresh_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
            
            user_session = UserSession(
                user_id=user.id,
                session_token=session_token,
                refresh_token=refresh_token,
                status=SessionStatus.ACTIVE.value,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=expires_at
            )
            
            session.add(user_session)
            session.flush()  # Get the session ID
            
            # Generate JWT tokens
            access_token = self._generate_access_token(user, user_session)
            refresh_jwt = self._generate_refresh_token(user, user_session)
            
            return user_session, access_token, refresh_jwt
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            return None
    
    def _generate_access_token(self, user: User, user_session: UserSession) -> str:
        """Generate JWT access token"""
        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.access_token_expire_minutes)
        
        # Get user roles and permissions
        roles = [role.name for role in user.roles]
        permissions = []
        for role in user.roles:
            permissions.extend([perm.name for perm in role.permissions])
        permissions = list(set(permissions))  # Remove duplicates
        
        payload = {
            "user_id": str(user.id),
            "session_id": str(user_session.id),
            "tenant_id": user.tenant_id,
            "email": user.email,
            "roles": roles,
            "permissions": permissions,
            "type": "access",
            "iat": now,
            "exp": expires
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _generate_refresh_token(self, user: User, user_session: UserSession) -> str:
        """Generate JWT refresh token"""
        now = datetime.utcnow()
        expires = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "user_id": str(user.id),
            "session_id": str(user_session.id),
            "tenant_id": user.tenant_id,
            "type": "refresh",
            "iat": now,
            "exp": expires
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def validate_access_token(self, token: str) -> Optional[TokenPayload]:
        """Validate JWT access token and return payload"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            if payload.get("type") != "access":
                return None
            
            # Check if session is still active
            with get_session_context() as session:
                user_session = session.query(UserSession).filter_by(
                    id=payload["session_id"]
                ).first()
                
                if not user_session or not user_session.is_active:
                    return None
                
                # Update last activity
                user_session.last_activity = datetime.utcnow()
                session.commit()
            
            return TokenPayload(
                user_id=payload["user_id"],
                session_id=payload["session_id"],
                tenant_id=payload["tenant_id"],
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                type=payload["type"]
            )
            
        except jwt.ExpiredSignatureError:
            logger.debug("Access token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            if payload.get("type") != "refresh":
                return None
            
            with get_session_context() as session:
                # Get user and session
                user = session.query(User).filter_by(id=payload["user_id"]).first()
                user_session = session.query(UserSession).filter_by(
                    id=payload["session_id"]
                ).first()
                
                if not user or not user_session or not user_session.is_active:
                    return None
                
                # Generate new tokens
                new_access_token = self._generate_access_token(user, user_session)
                new_refresh_token = self._generate_refresh_token(user, user_session)
                
                # Update session
                user_session.refresh_token = secrets.token_urlsafe(32)
                user_session.last_activity = datetime.utcnow()
                
                session.commit()
                
                return new_access_token, new_refresh_token
                
        except jwt.ExpiredSignatureError:
            logger.debug("Refresh token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return None
    
    def logout_user(self, session_id: str, ip_address: str = None, user_agent: str = None) -> bool:
        """Logout user by revoking session"""
        try:
            with get_session_context() as session:
                user_session = session.query(UserSession).filter_by(id=session_id).first()
                
                if not user_session:
                    return False
                
                # Revoke session
                user_session.status = SessionStatus.REVOKED.value
                user_session.revoked_at = datetime.utcnow()
                
                # Log logout
                self._log_audit_event(
                    session, user_session.user_id, "logout", "authentication", "success",
                    ip_address, user_agent, user_session.session_token, 
                    user_session.user.tenant_id,
                    {"session_id": session_id}
                )
                
                session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def setup_2fa(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Setup 2FA for user and return QR code"""
        try:
            with get_session_context() as session:
                user = session.query(User).filter_by(id=user_id).first()
                
                if not user:
                    return None
                
                # Generate TOTP secret
                secret = pyotp.random_base32()
                
                # Create TOTP URI
                totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                    name=user.email,
                    issuer_name=self.totp_issuer
                )
                
                # Generate QR code
                qr = qrcode.QRCode(version=1, box_size=10, border=5)
                qr.add_data(totp_uri)
                qr.make(fit=True)
                
                img = qr.make_image(fill_color="black", back_color="white")
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                # Store secret (not yet enabled)
                user.totp_secret = secret
                session.commit()
                
                return {
                    "secret": secret,
                    "qr_code": f"data:image/png;base64,{qr_code_base64}",
                    "manual_entry_key": secret
                }
                
        except Exception as e:
            logger.error(f"2FA setup error: {e}")
            return None
    
    def enable_2fa(self, user_id: str, totp_code: str) -> bool:
        """Enable 2FA after verifying TOTP code"""
        try:
            with get_session_context() as session:
                user = session.query(User).filter_by(id=user_id).first()
                
                if not user or not user.totp_secret:
                    return False
                
                # Verify TOTP code
                if not self._verify_totp(user.totp_secret, totp_code):
                    return False
                
                # Enable 2FA
                user.is_2fa_enabled = True
                
                # Generate backup codes
                backup_codes = [secrets.token_hex(4) for _ in range(10)]
                user.backup_codes = backup_codes
                
                session.commit()
                
                logger.info(f"2FA enabled for user {user.email}")
                return True
                
        except Exception as e:
            logger.error(f"2FA enable error: {e}")
            return False
    
    def _verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=1)  # Allow 1 window tolerance
        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            return False
    
    def _log_audit_event(self, session: Session, user_id: str, event_type: str, 
                        resource: str, result: str, ip_address: str = None,
                        user_agent: str = None, session_token: str = None,
                        tenant_id: str = None, details: Dict = None):
        """Log audit event for HIPAA compliance"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                resource=resource,
                action=event_type,
                result=result,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_token,
                tenant_id=tenant_id or "unknown",
                details=details or {}
            )
            
            session.add(audit_log)
            
        except Exception as e:
            logger.error(f"Audit logging error: {e}")
    
    def _log_security_event(self, session: Session, event_type: str, severity: str,
                           category: str, ip_address: str = None, user_agent: str = None,
                           user_id: str = None, context: Dict = None):
        """Log security event for threat monitoring"""
        try:
            security_event = SecurityEvent(
                event_type=event_type,
                severity=severity,
                category=category,
                source_ip=ip_address,
                user_agent=user_agent,
                user_id=user_id,
                tenant_id=context.get("tenant_id", "unknown") if context else "unknown",
                context=context or {}
            )
            
            session.add(security_event)
            
        except Exception as e:
            logger.error(f"Security event logging error: {e}")

# Global auth manager instance
auth_manager = EnhancedAuthManager()
