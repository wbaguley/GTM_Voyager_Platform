from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import logging

class GTMVoyagerAPI:
    """Main FastAPI application for GTM Voyager Platform."""
    
    def __init__(self):
        """Initialize the GTM Voyager API."""
        self.app = FastAPI(
            title="GTM Voyager Platform API",
            description="Voice-first business automation platform",
            version="1.0.0"
        )
        
        self.logger = self._setup_logger()
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the API."""
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
        """Set up FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self):
        """Set up API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "GTM Voyager Platform API",
                "version": "1.0.0",
                "status": "active"
            }
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "service": "GTM Voyager Platform"
            }
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app

app = GTMVoyagerAPI().get_app()