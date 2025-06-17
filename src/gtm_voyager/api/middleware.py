"""
GTM Voyager Platform - Custom Middleware
Security, rate limiting, and audit logging middleware for FastAPI.
"""

import time
import logging
from datetime import datetime
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .auth import auth_manager
from ..database.config import get_session_context
from ..database.models import AuditLog, SecurityEvent
from ..utils.security import security_manager
from .dependencies import get_client_info

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for request validation and threat detection"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger('SecurityMiddleware')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks"""
        start_time = time.time()
        
        try:
            # Skip ALL security processing for docs-related endpoints
            if (request.url.path.startswith("/docs") or 
                request.url.path.startswith("/redoc") or 
                request.url.path.startswith("/openapi.json") or
                "swagger" in request.url.path.lower() or
                "redoc" in request.url.path.lower()):
                
                # Process request without any security headers
                response = await call_next(request)
                
                # Add only timing header
                process_time = time.time() - start_time
                response.headers["X-Process-Time"] = str(process_time)
                
                return response
            
            # Get client information
            client_info = get_client_info(request)
            
            # Validate IP address
            if not security_manager.validate_ip_address(client_info["ip_address"]):
                self.logger.warning(f"Invalid IP address: {client_info['ip_address']}")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid request source"}
                )
            
            # Check for suspicious activity
            risk_assessment = security_manager.detect_suspicious_activity(
                client_info["ip_address"], "request"
            )
            
            # Block high-risk requests
            if risk_assessment["risk_level"] in ["critical", "high"]:
                self.logger.warning(
                    f"Blocked high-risk request from {client_info['ip_address']}: "
                    f"Risk score {risk_assessment['risk_score']}"
                )
                
                # Log security event
                await self._log_security_event(
                    "high_risk_request_blocked", "high", "security",
                    client_info, risk_assessment
                )
                
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Request blocked for security reasons"}
                )
            
            # Add security context to request
            request.state.client_info = client_info
            request.state.risk_assessment = risk_assessment
            request.state.start_time = start_time
            
            # Process request
            response = await call_next(request)
            
            # Add strict security headers for all non-docs endpoints
            security_headers = security_manager.get_security_headers()
            for header, value in security_headers.items():
                response.headers[header] = value
            
            # Add timing header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Security middleware error: {e}")
            # Don't block request on middleware errors
            return await call_next(request)
    
    async def _log_security_event(self, event_type: str, severity: str, 
                                 category: str, client_info: dict, 
                                 risk_assessment: dict):
        """Log security event to database"""
        try:
            with get_session_context() as session:
                security_event = SecurityEvent(
                    event_type=event_type,
                    severity=severity,
                    category=category,
                    source_ip=client_info["ip_address"],
                    user_agent=client_info["user_agent"],
                    tenant_id="system",
                    confidence_score=risk_assessment["risk_score"],
                    context={
                        "risk_assessment": risk_assessment,
                        "client_info": client_info
                    }
                )
                session.add(security_event)
                session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log security event: {e}")

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger('RateLimitMiddleware')
        
        # Rate limit exemptions
        self.exempt_paths = {
            "/health", "/", "/docs", "/redoc", "/openapi.json"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests"""
        try:
            # Skip rate limiting for exempt paths
            if request.url.path in self.exempt_paths:
                return await call_next(request)
            
            # Get client info
            client_info = getattr(request.state, 'client_info', None)
            if not client_info:
                client_info = get_client_info(request)
            
            # Try to get user from token for authenticated rate limiting
            user_id = None
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                token_payload = auth_manager.validate_access_token(token)
                if token_payload:
                    user_id = token_payload.user_id
            
            # Use user ID if available, otherwise IP address
            identifier = user_id or client_info["ip_address"]
            
            # Different limits for authenticated vs anonymous users
            if user_id:
                max_requests = 200  # Higher limit for authenticated users
                window_seconds = 300  # 5 minutes
            else:
                max_requests = 100  # Lower limit for anonymous users
                window_seconds = 300  # 5 minutes
            
            # Check rate limit
            is_allowed, rate_info = security_manager.check_rate_limit(
                identifier, max_requests, window_seconds
            )
            
            if not is_allowed:
                self.logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{rate_info['current_count']}/{rate_info['max_requests']}"
                )
                
                # Log rate limit event
                await self._log_rate_limit_event(identifier, client_info, rate_info)
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded",
                        "retry_after": rate_info["retry_after"]
                    },
                    headers={
                        "Retry-After": str(rate_info["retry_after"]),
                        "X-RateLimit-Limit": str(rate_info["max_requests"]),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": rate_info["reset_time"]
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(rate_info["max_requests"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info.get("remaining", 0))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Rate limit middleware error: {e}")
            # Don't block request on middleware errors
            return await call_next(request)
    
    async def _log_rate_limit_event(self, identifier: str, client_info: dict, 
                                   rate_info: dict):
        """Log rate limit exceeded event"""
        try:
            with get_session_context() as session:
                security_event = SecurityEvent(
                    event_type="rate_limit_exceeded",
                    severity="medium",
                    category="rate_limiting",
                    source_ip=client_info["ip_address"],
                    user_agent=client_info["user_agent"],
                    tenant_id="system",
                    context={
                        "identifier": identifier,
                        "rate_info": rate_info,
                        "client_info": client_info
                    }
                )
                session.add(security_event)
                session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log rate limit event: {e}")

class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware for HIPAA compliance"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger('AuditMiddleware')
        
        # Paths that should be audited
        self.audit_paths = {
            "/auth/login", "/auth/logout", "/auth/refresh",
            "/dental/records", "/voice/process", "/admin/"
        }
        
        # Sensitive paths that require detailed logging
        self.sensitive_paths = {
            "/dental/records", "/voice/process", "/admin/users"
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log requests for audit trail"""
        start_time = time.time()
        
        try:
            # Check if this path should be audited
            should_audit = any(
                request.url.path.startswith(path) for path in self.audit_paths
            )
            
            if not should_audit:
                return await call_next(request)
            
            # Get client info
            client_info = getattr(request.state, 'client_info', None)
            if not client_info:
                client_info = get_client_info(request)
            
            # Try to get user from token
            user_id = None
            session_id = None
            tenant_id = "unknown"
            
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                token_payload = auth_manager.validate_access_token(token)
                if token_payload:
                    user_id = token_payload.user_id
                    session_id = token_payload.session_id
                    tenant_id = token_payload.tenant_id
            
            # Process request
            response = await call_next(request)
            
            # Determine result
            if response.status_code < 400:
                result = "success"
            elif response.status_code < 500:
                result = "client_error"
            else:
                result = "server_error"
            
            # Log audit event
            await self._log_audit_event(
                user_id=user_id,
                event_type=self._get_event_type(request.method, request.url.path),
                resource=self._get_resource(request.url.path),
                action=request.method.lower(),
                result=result,
                ip_address=client_info["ip_address"],
                user_agent=client_info["user_agent"],
                session_id=session_id,
                tenant_id=tenant_id,
                details={
                    "path": str(request.url.path),
                    "method": request.method,
                    "status_code": response.status_code,
                    "process_time": time.time() - start_time,
                    "query_params": dict(request.query_params),
                    "is_sensitive": any(
                        request.url.path.startswith(path) 
                        for path in self.sensitive_paths
                    )
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Audit middleware error: {e}")
            # Don't block request on middleware errors
            return await call_next(request)
    
    def _get_event_type(self, method: str, path: str) -> str:
        """Determine event type from method and path"""
        if "/auth/login" in path:
            return "login"
        elif "/auth/logout" in path:
            return "logout"
        elif "/dental/records" in path:
            return "dental_record_access"
        elif "/voice/process" in path:
            return "voice_processing"
        elif "/admin/" in path:
            return "admin_access"
        else:
            return f"{method.lower()}_request"
    
    def _get_resource(self, path: str) -> str:
        """Determine resource from path"""
        if "/auth/" in path:
            return "authentication"
        elif "/dental/" in path:
            return "dental_records"
        elif "/voice/" in path:
            return "voice_processing"
        elif "/admin/" in path:
            return "administration"
        else:
            return "api"
    
    async def _log_audit_event(self, user_id: str, event_type: str, resource: str,
                              action: str, result: str, ip_address: str,
                              user_agent: str, session_id: str, tenant_id: str,
                              details: dict):
        """Log audit event to database"""
        try:
            with get_session_context() as session:
                audit_log = AuditLog(
                    user_id=user_id,
                    event_type=event_type,
                    resource=resource,
                    action=action,
                    result=result,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    session_id=session_id,
                    tenant_id=tenant_id,
                    details=details
                )
                session.add(audit_log)
                session.commit()
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware for debugging and monitoring"""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger('RequestLogging')
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request details"""
        start_time = time.time()
        
        # Log request
        self.logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            self.logger.info(
                f"Response: {response.status_code} - "
                f"Time: {process_time:.3f}s - "
                f"Path: {request.url.path}"
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            self.logger.error(
                f"Request failed: {request.method} {request.url.path} - "
                f"Error: {str(e)} - Time: {process_time:.3f}s"
            )
            raise

