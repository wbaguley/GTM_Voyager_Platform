# Add these methods to your GTMVoyagerMCPServer class in src/gtm_voyager/api/mcp/server.py

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Add these methods to your existing GTMVoyagerMCPServer class:

async def handle_message(self, message: dict) -> dict:
    """Handle incoming MCP protocol messages"""
    try:
        method = message.get("method")
        message_id = message.get("id")
        params = message.get("params", {})
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "GTM Voyager MCP Server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            tools = await self.get_available_tools()
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "tools": tools
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Execute the tool
            result = await self.execute_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
        
        elif method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "status": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": message_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

async def get_available_tools(self) -> list:
    """Get list of available MCP tools"""
    try:
        from .tools import get_all_mcp_tools
        tools = await get_all_mcp_tools()
        return tools
    except Exception as e:
        logger.error(f"Error getting available tools: {e}")
        return []

async def execute_tool(self, tool_name: str, arguments: dict) -> str:
    """Execute a specific tool with given arguments"""
    try:
        from .tools import execute_mcp_tool
        result = await execute_mcp_tool(tool_name, arguments)
        return result
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise Exception(f"Tool execution failed: {str(e)}")

