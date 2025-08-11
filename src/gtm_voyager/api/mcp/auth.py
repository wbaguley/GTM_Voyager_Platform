"""
MCP Authentication for GTM Voyager Platform
Uses PyJWT for token-based authentication
"""

import jwt
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from ...config import mcp_config

logger = logging.getLogger(__name__)

@dataclass
class MCPAuthResult:
    """Result of MCP authentication attempt"""
    success: bool
    client_id: Optional[str] = None
    error: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

async def authenticate_mcp_connection(connection, params: Dict[str, Any]) -> MCPAuthResult:
    """Authenticate MCP connection"""
    try:
        # Extract authentication information
        client_info = params.get("clientInfo", {})
        client_name = client_info.get("name", "unknown")
        
        # Extract auth token
        auth_token = await extract_auth_token(connection, params)
        
        if not auth_token:
            return MCPAuthResult(
                success=False,
                error="No authentication token provided"
            )
        
        # Validate token
        token_data = validate_mcp_token(auth_token)
        if not token_data:
            return MCPAuthResult(
                success=False,
                error="Invalid authentication token"
            )
        
        # Extract client permissions
        permissions = token_data.get("permissions", {
            "voice_processing": True,
            "ai_agents": True,
            "workflow_automation": True,
            "database_read": True,
            "database_write": False
        })
        
        logger.info(f"MCP client authenticated: {client_name}")
        
        return MCPAuthResult(
            success=True,
            client_id=token_data.get("client_id", client_name),
            permissions=permissions
        )
    
    except Exception as e:
        logger.error(f"MCP authentication error: {e}")
        return MCPAuthResult(
            success=False,
            error=f"Authentication failed: {str(e)}"
        )

async def extract_auth_token(connection, params: Dict[str, Any]) -> Optional[str]:
    """Extract authentication token from connection or parameters"""
    
    # Check for token in client info
    client_info = params.get("clientInfo", {})
    if "authToken" in client_info:
        return client_info["authToken"]
    
    # For development/testing, allow a default token
    if mcp_config.MCP_AUTH_SECRET == "your-secure-mcp-secret-key-change-this-in-production":
        logger.warning("Using default MCP auth token - change this in production!")
        return "dev-token"
    
    return None

def validate_mcp_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate MCP authentication token"""
    try:
        # For development, accept simple tokens
        if token == "dev-token":
            return {
                "client_id": "development-client",
                "permissions": {
                    "voice_processing": True,
                    "ai_agents": True,
                    "workflow_automation": True,
                    "database_read": True,
                    "database_write": True
                },
                "expires": (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }
        
        # Try to decode as JWT token
        try:
            decoded = jwt.decode(
                token,
                mcp_config.MCP_AUTH_SECRET,
                algorithms=["HS256"]
            )
            return decoded
        except jwt.InvalidTokenError:
            pass
        
        return None
    
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None

def generate_mcp_token(client_id: str, permissions: Dict[str, bool] = None) -> str:
    """Generate MCP authentication token"""
    if permissions is None:
        permissions = {
            "voice_processing": True,
            "ai_agents": True,
            "workflow_automation": True,
            "database_read": True,
            "database_write": False
        }
    
    payload = {
        "client_id": client_id,
        "permissions": permissions,
        "issued_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    
    token = jwt.encode(payload, mcp_config.MCP_AUTH_SECRET, algorithm="HS256")
    return token

def get_test_token() -> str:
    """Generate a test token for development"""
    return generate_mcp_token(
        client_id="test-client",
        permissions={
            "voice_processing": True,
            "ai_agents": True,
            "workflow_automation": True,
            "database_read": True,
            "database_write": True
        }
    )