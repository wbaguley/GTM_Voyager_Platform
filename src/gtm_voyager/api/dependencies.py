"""
GTM Voyager Platform - FastAPI Dependencies
Authentication, authorization, and security dependencies for route protection.
"""

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Callable
from sqlalchemy.orm import Session
import logging

from .auth import auth_manager
from ..database.models import User
from ..database.config import get_session
from ..utils.security import security_manager

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)

def get_client_info(request: Request) -> dict:
    """Extract client information from request"""
    # Get real IP address (considering proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    real_ip = request.headers.get("X-Real-IP")
    
    if forwarded_for:
        # Take the first IP in the chain
        ip_address = forwarded_for.split(",")[0].strip()
    elif real_ip:
        ip_address = real_ip
    else:
        ip_address = request.client.host if request.client else "unknown"
    
    user_agent = request.headers.get("User-Agent", "unknown")
    
    return {
        "ip_address": ip_address,
        "user_agent": user_agent,
        "host": request.headers.get("Host", "unknown"),
        "referer": request.headers.get("Referer"),
        "origin": request.headers.get("Origin")
    }

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_session)
) -> Optional[User]:
    """
    Get current user from JWT token (optional - returns None if no valid token).
    Use this for routes that can work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        # Validate token
        token_payload = auth_manager.validate_access_token(credentials.credentials)
        if not token_payload:
            return None
        
        # Get user from database
        user = db.query(User).filter_by(id=token_payload.user_id).first()
        if not user or user.status != "active":
            return None
        
        return user
        
    except Exception as e:
        logger.warning(f"Optional authentication error: {e}")
        return None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_session)
) -> User:
    """
    Get current user from JWT token (required).
    Raises HTTPException if no valid token or user not found.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Validate token
        token_payload = auth_manager.validate_access_token(credentials.credentials)
        if not token_payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user from database
        user = db.query(User).filter_by(id=token_payload.user_id).first()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if user.status != "active":
            raise HTTPException(
                status_code=403,
                detail="Account is not active"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

def require_permission(permission: str) -> Callable:
    """
    Dependency factory that creates a dependency requiring a specific permission.
    
    Usage:
        @app.get("/admin/users")
        async def list_users(user: User = Depends(require_permission("users.read"))):
            ...
    """
    async def permission_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_dependency

def require_role(role: str) -> Callable:
    """
    Dependency factory that creates a dependency requiring a specific role.
    
    Usage:
        @app.get("/admin/dashboard")
        async def admin_dashboard(user: User = Depends(require_role("admin"))):
            ...
    """
    async def role_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.has_role(role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{role}' required"
            )
        return current_user
    
    return role_dependency

def require_any_permission(*permissions: str) -> Callable:
    """
    Dependency factory that requires ANY of the specified permissions.
    
    Usage:
        @app.get("/records")
        async def get_records(user: User = Depends(require_any_permission("records.read", "records.admin"))):
            ...
    """
    async def any_permission_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not any(current_user.has_permission(perm) for perm in permissions):
            raise HTTPException(
                status_code=403,
                detail=f"One of these permissions required: {', '.join(permissions)}"
            )
        return current_user
    
    return any_permission_dependency

def require_all_permissions(*permissions: str) -> Callable:
    """
    Dependency factory that requires ALL of the specified permissions.
    
    Usage:
        @app.delete("/admin/users/{user_id}")
        async def delete_user(user: User = Depends(require_all_permissions("users.delete", "admin.access"))):
            ...
    """
    async def all_permissions_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not all(current_user.has_permission(perm) for perm in permissions):
            raise HTTPException(
                status_code=403,
                detail=f"All of these permissions required: {', '.join(permissions)}"
            )
        return current_user
    
    return all_permissions_dependency

def require_tenant_access(tenant_id: str) -> Callable:
    """
    Dependency factory that ensures user has access to specific tenant.
    
    Usage:
        @app.get("/tenant/{tenant_id}/data")
        async def get_tenant_data(
            tenant_id: str,
            user: User = Depends(require_tenant_access(tenant_id))
        ):
            ...
    """
    async def tenant_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        # Super admins can access any tenant
        if current_user.has_role("super_admin"):
            return current_user
        
        # Regular users can only access their own tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=403,
                detail="Access to this tenant not allowed"
            )
        
        return current_user
    
    return tenant_dependency

async def validate_rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
) -> None:
    """
    Validate rate limiting for the request.
    Uses user ID if authenticated, otherwise uses IP address.
    """
    try:
        client_info = get_client_info(request)
        
        # Use user ID if authenticated, otherwise IP address
        identifier = str(current_user.id) if current_user else client_info["ip_address"]
        
        # Check rate limit
        is_allowed, rate_info = security_manager.check_rate_limit(identifier)
        
        if not is_allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "Retry-After": str(rate_info["retry_after"]),
                    "X-RateLimit-Limit": str(rate_info["max_requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": rate_info["reset_time"]
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rate limit validation error: {e}")
        # Don't block request on rate limit errors
        pass

async def validate_csrf_token(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Validate CSRF token for state-changing operations.
    Use this dependency for POST, PUT, DELETE routes.
    """
    try:
        # Skip CSRF validation for API requests with proper authentication
        if request.headers.get("Content-Type", "").startswith("application/json"):
            return
        
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            # Try to get from form data
            form_data = await request.form()
            csrf_token = form_data.get("csrf_token")
        
        if not csrf_token:
            raise HTTPException(
                status_code=403,
                detail="CSRF token required"
            )
        
        # Get session ID from current user's token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            token_payload = auth_manager.validate_access_token(token)
            
            if token_payload:
                is_valid = security_manager.validate_csrf_token(
                    csrf_token, token_payload.session_id
                )
                
                if not is_valid:
                    raise HTTPException(
                        status_code=403,
                        detail="Invalid CSRF token"
                    )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSRF validation error: {e}")
        raise HTTPException(
            status_code=403,
            detail="CSRF validation failed"
        )

def require_2fa_verified() -> Callable:
    """
    Dependency that requires user to have 2FA enabled and verified.
    Use for sensitive operations.
    """
    async def two_fa_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.is_2fa_enabled:
            raise HTTPException(
                status_code=403,
                detail="Two-factor authentication required for this operation"
            )
        return current_user
    
    return two_fa_dependency

async def get_pagination_params(
    page: int = 1,
    size: int = 20,
    max_size: int = 100
) -> dict:
    """
    Get pagination parameters with validation.
    
    Args:
        page: Page number (1-based)
        size: Items per page
        max_size: Maximum allowed page size
    
    Returns:
        Dictionary with offset, limit, page, and size
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    
    if size < 1:
        raise HTTPException(status_code=400, detail="Size must be >= 1")
    
    if size > max_size:
        raise HTTPException(status_code=400, detail=f"Size must be <= {max_size}")
    
    offset = (page - 1) * size
    
    return {
        "offset": offset,
        "limit": size,
        "page": page,
        "size": size
    }

# Convenience dependencies for common permission combinations
require_admin = require_role("admin")
require_super_admin = require_role("super_admin")
require_user_read = require_permission("users.read")
require_user_write = require_permission("users.write")
require_dental_read = require_permission("dental_records.read")
require_dental_write = require_permission("dental_records.write")
require_voice_process = require_permission("voice.process")
require_system_admin = require_permission("system.admin")
