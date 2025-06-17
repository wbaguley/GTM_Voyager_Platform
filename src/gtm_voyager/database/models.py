"""
GTM Voyager Platform - Database Models
Authentication, user management, and security models for multi-tenant platform.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

Base = declarative_base()

# Association tables for many-to-many relationships
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions', 
    Base.metadata,
    Column('role_id', UUID(as_uuid=True), ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', UUID(as_uuid=True), ForeignKey('permissions.id'), primary_key=True)
)

class UserStatus(enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class SessionStatus(enum.Enum):
    """Session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    
    # Status and verification
    status = Column(String(50), default=UserStatus.PENDING_VERIFICATION.value)
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255), nullable=True)
    
    # 2FA settings
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(255), nullable=True)
    backup_codes = Column(JSON, nullable=True)  # List of backup codes
    
    # Multi-tenant support
    tenant_id = Column(String(100), nullable=False, index=True)
    organization = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, default=datetime.utcnow)
    
    # Password policy
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(email='{self.email}', tenant='{self.tenant_id}')>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_locked(self):
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission"""
        for role in self.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        return False
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)

class Role(Base):
    """Role model for role-based access control"""
    __tablename__ = 'roles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Multi-tenant support
    tenant_id = Column(String(100), nullable=True, index=True)  # None for global roles
    
    # Metadata
    is_system_role = Column(Boolean, default=False)  # Cannot be deleted
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def __repr__(self):
        return f"<Role(name='{self.name}', tenant='{self.tenant_id}')>"

class Permission(Base):
    """Permission model for granular access control"""
    __tablename__ = 'permissions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    resource = Column(String(100), nullable=False)  # e.g., 'users', 'dental_records'
    action = Column(String(50), nullable=False)     # e.g., 'read', 'write', 'delete'
    
    # Metadata
    is_system_permission = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __repr__(self):
        return f"<Permission(name='{self.name}', resource='{self.resource}', action='{self.action}')>"

class UserSession(Base):
    """User session model for JWT and session management"""
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session details
    status = Column(String(50), default=SessionStatus.ACTIVE.value)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', status='{self.status}')>"
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_active(self):
        return self.status == SessionStatus.ACTIVE.value and not self.is_expired

class APIKey(Base):
    """API Key model for programmatic access"""
    __tablename__ = 'api_keys'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String(255), nullable=False)  # Human-readable name
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(20), nullable=False)  # First few chars for identification
    
    # Permissions and restrictions
    scopes = Column(JSON, nullable=True)  # List of allowed scopes
    rate_limit = Column(Integer, nullable=True)  # Requests per minute
    allowed_ips = Column(JSON, nullable=True)  # List of allowed IP addresses
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<APIKey(name='{self.name}', user_id='{self.user_id}')>"
    
    @property
    def is_expired(self):
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self):
        return self.is_active and not self.is_expired

class AuditLog(Base):
    """Audit log model for HIPAA compliance and security monitoring"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # login, logout, data_access, etc.
    resource = Column(String(100), nullable=True)  # What was accessed
    action = Column(String(50), nullable=False)    # What action was performed
    result = Column(String(50), nullable=False)    # success, failure, etc.
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Additional data
    details = Column(JSON, nullable=True)  # Additional context data
    risk_score = Column(Integer, nullable=True)  # 0-100 risk assessment
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(event_type='{self.event_type}', user_id='{self.user_id}')>"

class SecurityEvent(Base):
    """Security event model for threat detection and monitoring"""
    __tablename__ = 'security_events'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event classification
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    category = Column(String(50), nullable=False)  # authentication, authorization, data_access
    
    # Event details
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Detection details
    rule_triggered = Column(String(255), nullable=True)
    confidence_score = Column(Integer, nullable=True)  # 0-100
    false_positive = Column(Boolean, default=False)
    
    # Response
    status = Column(String(50), default='open')  # open, investigating, resolved, false_positive
    assigned_to = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Additional data
    raw_data = Column(JSON, nullable=True)
    context = Column(JSON, nullable=True)
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<SecurityEvent(event_type='{self.event_type}', severity='{self.severity}')>"

# Database utility functions
def create_default_roles_and_permissions():
    """Create default roles and permissions for the system"""
    default_permissions = [
        # User management
        ("users.read", "Read Users", "View user information", "users", "read"),
        ("users.write", "Write Users", "Create and update users", "users", "write"),
        ("users.delete", "Delete Users", "Delete user accounts", "users", "delete"),
        
        # Role management
        ("roles.read", "Read Roles", "View roles and permissions", "roles", "read"),
        ("roles.write", "Write Roles", "Create and update roles", "roles", "write"),
        ("roles.delete", "Delete Roles", "Delete roles", "roles", "delete"),
        
        # Dental records
        ("dental_records.read", "Read Dental Records", "View patient dental records", "dental_records", "read"),
        ("dental_records.write", "Write Dental Records", "Create and update dental records", "dental_records", "write"),
        ("dental_records.delete", "Delete Dental Records", "Delete dental records", "dental_records", "delete"),
        
        # Voice processing
        ("voice.process", "Process Voice", "Process voice recordings", "voice", "process"),
        ("voice.transcribe", "Transcribe Voice", "Transcribe voice to text", "voice", "transcribe"),
        
        # System administration
        ("system.admin", "System Admin", "Full system administration", "system", "admin"),
        ("audit.read", "Read Audit Logs", "View audit logs", "audit", "read"),
        ("security.monitor", "Security Monitor", "Monitor security events", "security", "monitor"),
    ]
    
    default_roles = [
        # System roles
        ("super_admin", "Super Administrator", "Full system access", True),
        ("system_admin", "System Administrator", "System administration access", True),
        ("security_admin", "Security Administrator", "Security and audit access", True),
        
        # Dental practice roles
        ("practice_owner", "Practice Owner", "Full practice management access", False),
        ("dentist", "Dentist", "Clinical access and patient management", False),
        ("dental_hygienist", "Dental Hygienist", "Limited clinical access", False),
        ("office_manager", "Office Manager", "Administrative and scheduling access", False),
        ("receptionist", "Receptionist", "Front desk and scheduling access", False),
        ("patient", "Patient", "Patient portal access", False),
    ]
    
    return default_permissions, default_roles
