"""
MCP Resources for GTM Voyager Platform
Provides data access via MCP protocol
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

async def get_all_mcp_resources() -> List[Dict[str, Any]]:
    """Get all available MCP resources"""
    return [
        {
            "uri": "gtm://config/system",
            "name": "System Configuration",
            "description": "GTM Voyager system configuration"
        },
        {
            "uri": "gtm://status/health",
            "name": "System Health",
            "description": "Current system health status"
        }
    ]

async def get_resources_list() -> List[Dict[str, Any]]:
    """Get resources list in MCP format"""
    return await get_all_mcp_resources()

async def read_resource(uri: str) -> Dict[str, Any]:
    """Read a specific resource"""
    try:
        if uri == "gtm://config/system":
            return {
                "mcp_enabled": True,
                "voice_processing": "available",
                "ai_agents": ["dental", "hvac", "electrical"],
                "workflow_automation": "available"
            }
        elif uri == "gtm://status/health":
            return {
                "status": "healthy",
                "uptime": "running",
                "connections": 0
            }
        else:
            return {"error": f"Resource not found: {uri}"}
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return {"error": str(e)}