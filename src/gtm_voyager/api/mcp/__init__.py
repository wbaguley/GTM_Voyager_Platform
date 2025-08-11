"""
GTM Voyager MCP (Model Context Protocol) Integration
Enables voice-first AI interactions through 11.ai and other MCP clients
"""

from .server import GTMVoyagerMCPServer, mcp_server, initialize, start_server, stop_server
from .tools import get_all_mcp_tools, execute_tool
from .resources import get_all_mcp_resources, get_resource
from .auth import MCPAuthenticator

__all__ = [
    "GTMVoyagerMCPServer",
    "mcp_server", 
    "initialize",
    "start_server",
    "stop_server",
    "get_all_mcp_tools",
    "execute_tool",
    "get_all_mcp_resources", 
    "get_resource",
    "MCPAuthenticator"
]