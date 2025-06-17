"""
GTM Voyager Platform - Enhanced Main API
FastAPI application with integrated authentication, security, and enterprise features.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
import logging
import time
from datetime import datetime

from .auth import auth_manager, AuthResult, TokenPayload
from ..database.models import User
from ..database.config import get_session, test_connection
from ..utils.security import security_manager
from .dependencies import get_current_user, require_permission, get_client_info
from .middleware import SecurityMiddleware, RateLimitMiddleware, AuditMiddleware

logger = logging.getLogger(__name__)

class GTMVoyagerAPI:
    """Enhanced FastAPI application for GTM Voyager Platform with authentication"""
    
    def __init__(self):
        """Initialize the enhanced GTM Voyager API"""
        self.app = FastAPI(
            title="GTM Voyager Platform API",
            description="Voice-first business automation platform with enterprise security",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        self.logger = self._setup_logger()
        self.security = HTTPBearer(auto_error=False)
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_error_handlers()
        
        self.logger.info("Enhanced GTM Voyager API initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the API"""
        logger = logging.getLogger('GTMVoyagerAPI')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_middleware(self):
        """Set up FastAPI middleware with security enhancements"""
        
        # Security middleware (custom)
        self.app.add_middleware(SecurityMiddleware)

        # Rate limiting middleware (custom)
        self.app.add_middleware(RateLimitMiddleware)
        
        # Audit logging middleware (custom)
        self.app.add_middleware(AuditMiddleware)
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_error_handlers(self):
        """Set up custom error handlers"""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException ):
            """Handle HTTP exceptions with security headers"""
            headers = security_manager.get_security_headers()
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()},
                headers=headers
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions"""
            self.logger.error(f"Unhandled exception: {exc}", exc_info=True)
            headers = security_manager.get_security_headers()
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "timestamp": datetime.utcnow().isoformat()},
                headers=headers
            )
    
    def _setup_routes(self):
        """Set up API routes with authentication"""
        
        # Public routes (no authentication required)
        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return {
                "message": "GTM Voyager Platform API",
                "version": "2.0.0",
                "status": "active",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint with database connectivity"""
            db_status = "connected" if test_connection() else "disconnected"
            return {
                "status": "healthy",
                "service": "GTM Voyager Platform",
                "database": db_status,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Authentication routes
        @self.app.post("/auth/login")
        async def login(
            request: Request,
            credentials: Dict[str, Any]
        ):
            """User login with email/password and optional 2FA"""
            try:
                email = credentials.get("email", "").strip().lower()
                password = credentials.get("password", "")
                totp_code = credentials.get("totp_code")
                
                if not email or not password:
                    raise HTTPException(status_code=400, detail="Email and password required")
                
                # Get client info
                client_info = get_client_info(request)
                
                # Authenticate user
                auth_result = auth_manager.authenticate_user(
                    email=email,
                    password=password,
                    ip_address=client_info["ip_address"],
                    user_agent=client_info["user_agent"],
                    totp_code=totp_code
                )
                
                if not auth_result.success:
                    # Log failed attempt
                    self.logger.warning(f"Failed login attempt for {email} from {client_info['ip_address']}")
                    
                    status_code = 401
                    if auth_result.requires_2fa:
                        status_code = 202  # Accepted, but 2FA required
                    
                    raise HTTPException(
                        status_code=status_code,
                        detail=auth_result.error_message
                    )
                
                # Successful login
                response_data = {
                    "access_token": auth_result.access_token,
                    "refresh_token": auth_result.refresh_token,
                    "token_type": "bearer",
                    "expires_in": auth_manager.access_token_expire_minutes * 60,
                    "message": "Login successful"
                }
                
                self.logger.info(f"Successful login for {email}")
                return response_data
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Login error: {e}")
                raise HTTPException(status_code=500, detail="Authentication service error")
        
        @self.app.post("/auth/refresh")
        async def refresh_token(refresh_data: Dict[str, str]):
            """Refresh access token using refresh token"""
            try:
                refresh_token = refresh_data.get("refresh_token")
                if not refresh_token:
                    raise HTTPException(status_code=400, detail="Refresh token required")
                
                tokens = auth_manager.refresh_access_token(refresh_token)
                if not tokens:
                    raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
                
                access_token, new_refresh_token = tokens
                
                return {
                    "access_token": access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer",
                    "expires_in": auth_manager.access_token_expire_minutes * 60
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Token refresh error: {e}")
                raise HTTPException(status_code=500, detail="Token refresh service error")
        
        @self.app.post("/auth/logout")
        async def logout(
            request: Request,
            current_user: User = Depends(get_current_user)
        ):
            """User logout"""
            try:
                # Get session ID from token
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    token_payload = auth_manager.validate_access_token(token)
                    
                    if token_payload:
                        client_info = get_client_info(request)
                        success = auth_manager.logout_user(
                            session_id=token_payload.session_id,
                            ip_address=client_info["ip_address"],
                            user_agent=client_info["user_agent"]
                        )
                        
                        if success:
                            return {"message": "Logged out successfully"}
                
                return {"message": "Logout completed"}
                
            except Exception as e:
                self.logger.error(f"Logout error: {e}")
                return {"message": "Logout completed"}  # Always return success for logout
        
        # 2FA routes
        @self.app.post("/auth/2fa/setup")
        async def setup_2fa(current_user: User = Depends(get_current_user)):
            """Setup 2FA for current user"""
            try:
                setup_data = auth_manager.setup_2fa(str(current_user.id))
                if not setup_data:
                    raise HTTPException(status_code=500, detail="Failed to setup 2FA")
                
                return {
                    "qr_code": setup_data["qr_code"],
                    "manual_entry_key": setup_data["manual_entry_key"],
                    "message": "Scan QR code with authenticator app and verify with code"
                }
                
            except Exception as e:
                self.logger.error(f"2FA setup error: {e}")
                raise HTTPException(status_code=500, detail="2FA setup service error")
        
        @self.app.post("/auth/2fa/enable")
        async def enable_2fa(
            verification_data: Dict[str, str],
            current_user: User = Depends(get_current_user)
        ):
            """Enable 2FA after verification"""
            try:
                totp_code = verification_data.get("totp_code")
                if not totp_code:
                    raise HTTPException(status_code=400, detail="TOTP code required")
                
                success = auth_manager.enable_2fa(str(current_user.id), totp_code)
                if not success:
                    raise HTTPException(status_code=400, detail="Invalid TOTP code")
                
                return {"message": "2FA enabled successfully"}
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"2FA enable error: {e}")
                raise HTTPException(status_code=500, detail="2FA enable service error")
        
        # Protected routes (require authentication)
        @self.app.get("/auth/me")
        async def get_current_user_info(current_user: User = Depends(get_current_user)):
            """Get current user information"""
            return {
                "id": str(current_user.id),
                "email": current_user.email,
                "username": current_user.username,
                "name": current_user.full_name,
                "status": current_user.status,
                "tenant_id": current_user.tenant_id,
                "organization": current_user.organization,
                "is_2fa_enabled": current_user.is_2fa_enabled,
                "roles": [role.name for role in current_user.roles],
                "permissions": list(set([
                    perm.name for role in current_user.roles 
                    for perm in role.permissions
                ])),
                "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
                "created_at": current_user.created_at.isoformat()
            }
        
        # Admin routes (require specific permissions)
        @self.app.get("/admin/users")
        async def list_users(
            current_user: User = Depends(require_permission("users.read")),
            db = Depends(get_session)
        ):
            """List users (admin only)"""
            try:
                users = db.query(User).filter_by(tenant_id=current_user.tenant_id).all()
                
                return {
                    "users": [
                        {
                            "id": str(user.id),
                            "email": user.email,
                            "name": user.full_name,
                            "status": user.status,
                            "roles": [role.name for role in user.roles],
                            "last_login": user.last_login.isoformat() if user.last_login else None,
                            "created_at": user.created_at.isoformat()
                        }
                        for user in users
                    ]
                }
                
            except Exception as e:
                self.logger.error(f"List users error: {e}")
                raise HTTPException(status_code=500, detail="Failed to retrieve users")
        
        # Voice processing routes (require voice permissions)
        @self.app.post("/voice/process")
        async def process_voice(
            file: UploadFile = File(...),
            current_user: User = Depends(require_permission("voice.process"))
        ):
            """Process voice file (requires voice.process permission)"""
            try:
                # Validate file
                if not file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.flac')):
                    raise HTTPException(status_code=400, detail="Unsupported audio format")
                
                if file.size > 25 * 1024 * 1024:  # 25MB limit
                    raise HTTPException(status_code=400, detail="File too large")
                
                # TODO: Integrate with your existing voice processing
                # This is where you'd call your enhanced audio processor
                
                return {
                    "message": "Voice processing initiated",
                    "file_name": file.filename,
                    "user_id": str(current_user.id),
                    "tenant_id": current_user.tenant_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Voice processing error: {e}")
                raise HTTPException(status_code=500, detail="Voice processing service error")
        
        # Dental records routes (require dental permissions)
        @self.app.get("/dental/records")
        async def get_dental_records(
            current_user: User = Depends(require_permission("dental_records.read"))
        ):
            """Get dental records (requires dental_records.read permission)"""
            try:
                # TODO: Integrate with your dental records system
                return {
                    "records": [],
                    "user_id": str(current_user.id),
                    "tenant_id": current_user.tenant_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"Dental records error: {e}")
                raise HTTPException(status_code=500, detail="Dental records service error")
        
        # System status routes
        @self.app.get("/system/status")
        async def system_status(
            current_user: User = Depends(require_permission("system.admin"))
        ):
            """Get system status (admin only)"""
            try:
                return {
                    "database": "connected" if test_connection() else "disconnected",
                    "authentication": "active",
                    "voice_processing": "active",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"System status error: {e}")
                raise HTTPException(status_code=500, detail="System status service error")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app

# Create the FastAPI application
app = GTMVoyagerAPI().get_app()

# Add security headers to all responses
@app.middleware("http" )
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Add security headers
    headers = security_manager.get_security_headers()
    for header, value in headers.items():
        response.headers[header] = value
    
    return response
