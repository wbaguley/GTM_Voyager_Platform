"""
GTM Voyager Platform - Enhanced Main API with CSP Fix
FastAPI application with CSP override for Swagger UI.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from typing import Dict, Any, Optional, List
import logging
import time
from datetime import datetime

from .auth import auth_manager, AuthResult, TokenPayload
from ..database.models import User
from ..database.config import get_session, test_connection
from ..utils.security import security_manager
from .dependencies import get_current_user, require_permission, get_client_info
from .endpoints import voice_router, agent_router, dental_router, workflow_router, status_router

logger = logging.getLogger(__name__)

class GTMVoyagerAPI:
    """Enhanced FastAPI application for GTM Voyager Platform with authentication"""
    
    def __init__(self):
        """Initialize the enhanced GTM Voyager API"""
        # Disable automatic docs to control CSP headers
        self.app = FastAPI(
            title="GTM Voyager Platform API",
            description="Voice-first business automation platform with enterprise security",
            version="2.0.0",
            docs_url=None,  # Disable automatic docs
            redoc_url=None,  # Disable automatic redoc
            openapi_url="/openapi.json"
        )

        self.logger = self._setup_logger()
        self.security = HTTPBearer(auto_error=False)
        
        self._setup_middleware()
        self._setup_routes()
        self._setup_error_handlers()
        self._setup_custom_docs()  # Add custom docs with CSP override
        
        self.logger.info("Enhanced GTM Voyager API initialized with CSP fix")
    
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
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add custom middleware to handle CSP for docs
        @self.app.middleware("http")
        async def override_csp_for_docs(request: Request, call_next):
            response = await call_next(request)
            
            # Check if this is a docs-related endpoint
            if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
                # Remove any existing CSP headers
                csp_headers_to_remove = []
                for header_name in response.headers:
                    if header_name.lower() == "content-security-policy":
                        csp_headers_to_remove.append(header_name)
                
                for header in csp_headers_to_remove:
                    del response.headers[header]
                
                # Set a permissive CSP for docs
                response.headers["Content-Security-Policy"] = (
                    "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:; "
                    "script-src * 'unsafe-inline' 'unsafe-eval'; "
                    "style-src * 'unsafe-inline'; "
                    "img-src * data: blob:; "
                    "font-src * data:; "
                    "connect-src *; "
                    "frame-src *;"
                )
            else:
                # For non-docs endpoints, use security headers
                headers = security_manager.get_security_headers()
                for header, value in headers.items():
                    if header != "Content-Security-Policy":  # Skip CSP for now
                        response.headers[header] = value
            
            return response
    
    def _setup_custom_docs(self):
        """Set up custom documentation endpoints with CSP override"""
        
        @self.app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html(request: Request):
            """Custom Swagger UI with CSP headers"""
            openapi_url = self.app.openapi_url
            title = self.app.title + " - Swagger UI"
            
            # Create custom HTML with inline Swagger UI
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>{title}</title>
                <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css">
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                </style>
            </head>
            <body>
                <div id="swagger-ui"></div>
                <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
                <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
                <script>
                    window.onload = function() {{
                        window.ui = SwaggerUIBundle({{
                            url: '{openapi_url}',
                            dom_id: '#swagger-ui',
                            presets: [
                                SwaggerUIBundle.presets.apis,
                                SwaggerUIStandalonePreset
                            ],
                            layout: "StandaloneLayout",
                            deepLinking: true,
                            showExtensions: true,
                            showCommonExtensions: true
                        }});
                    }};
                </script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html)
        
        @self.app.get("/redoc", include_in_schema=False)
        async def custom_redoc_html(request: Request):
            """Custom ReDoc with CSP headers"""
            openapi_url = self.app.openapi_url
            title = self.app.title + " - ReDoc"
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8"/>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>{title}</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                    }}
                </style>
            </head>
            <body>
                <redoc spec-url="{openapi_url}"></redoc>
                <script src="https://unpkg.com/redoc@2.0.0/bundles/redoc.standalone.js"></script>
            </body>
            </html>
            """
            
            return HTMLResponse(content=html)
    
    def _setup_error_handlers(self):
        """Set up custom error handlers"""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions with security headers"""
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()},
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions"""
            self.logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error", "timestamp": datetime.utcnow().isoformat()},
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
                    "user": {
                         "id": auth_result.user["id"],  # Already a string from our fix,
                        "email": auth_result.user["email"],
                         "name": f"{auth_result.user['first_name']} {auth_result.user['last_name']}"
                    }
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
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Logout error: {e}")
                raise HTTPException(status_code=500, detail="Logout service error")
        
        # Protected routes
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
                "created_at": current_user.created_at.isoformat()
            }
        
        # Include the endpoint routers
        self.app.include_router(voice_router, prefix="/api/v1", tags=["Voice Processing"])
        self.app.include_router(agent_router, prefix="/api/v1", tags=["Agent Management"])
        self.app.include_router(dental_router, prefix="/api/v1", tags=["Dental Workflows"])
        self.app.include_router(workflow_router, prefix="/api/v1", tags=["Workflow Management"])
        self.app.include_router(status_router, prefix="/api/v1", tags=["System Status"])
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app

# Create the FastAPI application
app = GTMVoyagerAPI().get_app()

