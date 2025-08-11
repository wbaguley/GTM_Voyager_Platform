"""
GTM Voyager MCP Server Implementation
Exposes GTM Voyager capabilities via Model Context Protocol
Built using standard libraries and websockets
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import websockets
from websockets.server import WebSocketServerProtocol
from dataclasses import dataclass
from datetime import datetime

# Import existing GTM Voyager components
from ...config import mcp_config

logger = logging.getLogger(__name__)

@dataclass
class MCPConnection:
    """Represents an active MCP connection"""
    websocket: WebSocketServerProtocol
    client_id: str
    authenticated: bool = False
    capabilities: Dict[str, Any] = None

class GTMVoyagerMCPServer:
    """
    MCP Server for GTM Voyager Platform
    Custom implementation of Model Context Protocol
    """
    
    def __init__(self):
        self.connections: Dict[str, MCPConnection] = {}
        self.tools_registered = False
        self.resources_registered = False
        self.server = None
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, mcp_config.MCP_LOG_LEVEL))
        logger.info("Initializing GTM Voyager MCP Server")
    
    async def initialize(self):
        """Initialize the MCP server with tools and resources"""
        try:
            await self.register_tools()
            await self.register_resources()
            logger.info("GTM Voyager MCP Server initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            raise
    
    async def register_tools(self):
        """Register MCP tools that expose GTM Voyager capabilities"""
        if self.tools_registered:
            return
        
        try:
            from .tools import get_all_mcp_tools
            tools = await get_all_mcp_tools()
            self.tools_registered = True
            logger.info(f"Registered {len(tools)} MCP tools")
        except ImportError:
            # Tools module not ready yet - that's OK for now
            self.tools_registered = True
            logger.info("Tools module not ready - will register later")
    
    async def register_resources(self):
        """Register MCP resources for data access"""
        if self.resources_registered:
            return
        
        from .resources import get_all_mcp_resources
        resources = await get_all_mcp_resources()
        self.resources_registered = True
        logger.info(f"Registered {len(resources)} MCP resources")
    
    async def start_server(self, host: str = "localhost", port: int = None):
        """Start the MCP WebSocket server"""
        if port is None:
            port = mcp_config.MCP_SERVER_PORT
        
        try:
            self.server = await websockets.serve(
                self.handle_connection,
                host,
                port,
                max_size=1024*1024,  # 1MB max message size
                max_queue=32,
                compression=None
            )
            logger.info(f"MCP Server started on ws://{host}:{port}")
            return self.server
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str = "/mcp"):
        """Handle incoming MCP WebSocket connections"""
        client_id = f"client_{id(websocket)}"
        connection = MCPConnection(websocket=websocket, client_id=client_id)
        
        try:
            # Store connection
            self.connections[client_id] = connection
            logger.info(f"New MCP connection: {client_id}")
            
            # Handle MCP protocol messages
            async for message in websocket:
                try:
                    await self.process_message(connection, message)
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    await self.send_error(connection, str(e))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"MCP connection closed: {client_id}")
        except Exception as e:
            logger.error(f"MCP connection error for {client_id}: {e}")
        finally:
            # Clean up connection
            if client_id in self.connections:
                del self.connections[client_id]
    
    async def process_message(self, connection: MCPConnection, message: str):
        """Process incoming MCP protocol messages"""
        try:
            data = json.loads(message)
            method = data.get("method")
            params = data.get("params", {})
            message_id = data.get("id")
            
            logger.debug(f"Processing MCP message: {method} from {connection.client_id}")
            
            # Handle different MCP methods
            if method == "initialize":
                await self.handle_initialize(connection, params, message_id)
            elif method == "tools/list":
                await self.handle_tools_list(connection, message_id)
            elif method == "tools/call":
                await self.handle_tool_call(connection, params, message_id)
            elif method == "resources/list":
                await self.handle_resources_list(connection, message_id)
            elif method == "resources/read":
                await self.handle_resource_read(connection, params, message_id)
            elif method == "ping":
                await self.handle_ping(connection, message_id)
            else:
                await self.send_error(connection, f"Unknown method: {method}", message_id)
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {connection.client_id}: {e}")
            await self.send_error(connection, "Invalid JSON message")
        except Exception as e:
            logger.error(f"Error processing message from {connection.client_id}: {e}")
            await self.send_error(connection, str(e))
    
    async def handle_ping(self, connection: MCPConnection, message_id: str):
        """Handle ping request"""
        response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "status": "pong",
                "timestamp": datetime.utcnow().isoformat(),
                "server": "gtm-voyager"
            }
        }
        await connection.websocket.send(json.dumps(response))
    
    async def handle_initialize(self, connection: MCPConnection, params: Dict[str, Any], message_id: str):
        """Handle MCP initialization"""
        try:
            # Authenticate connection
            from .auth import authenticate_mcp_connection
            auth_result = await authenticate_mcp_connection(connection, params)
            
            if not auth_result.success:
                await self.send_error(connection, auth_result.error, message_id)
                return
            
            connection.authenticated = True
            connection.capabilities = params.get("capabilities", {})
            
            # Send initialization response
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True, "listChanged": True},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "gtm-voyager",
                        "version": "1.0.0",
                        "description": "GTM Voyager Platform MCP Server"
                    }
                }
            }
            
            await connection.websocket.send(json.dumps(response))
            logger.info(f"MCP client {connection.client_id} initialized successfully")
        
        except Exception as e:
            logger.error(f"Initialization error for {connection.client_id}: {e}")
            await self.send_error(connection, str(e), message_id)
    
    async def handle_tools_list(self, connection: MCPConnection, message_id: str):
        """Handle tools list request"""
        if not connection.authenticated:
            await self.send_error(connection, "Not authenticated", message_id)
            return
        
        try:
            from .tools import get_tools_list
            tools = await get_tools_list()
            
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"tools": tools}
            }
            await connection.websocket.send(json.dumps(response))
        
        except ImportError:
            # Tools not implemented yet - return empty list
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"tools": []}
            }
            await connection.websocket.send(json.dumps(response))
        except Exception as e:
            logger.error(f"Error listing tools for {connection.client_id}: {e}")
            await self.send_error(connection, str(e), message_id)
    
    async def handle_tool_call(self, connection: MCPConnection, params: Dict[str, Any], message_id: str):
        """Handle tool call request"""
        if not connection.authenticated:
            await self.send_error(connection, "Not authenticated", message_id)
            return
        
        try:
            tool_name = params.get("name")
            tool_arguments = params.get("arguments", {})
            
            logger.info(f"Tool call: {tool_name} from {connection.client_id}")
            
            from .tools import execute_tool
            result = await execute_tool(tool_name, tool_arguments)
            
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            await connection.websocket.send(json.dumps(response))
        
        except ImportError:
            await self.send_error(connection, "Tools not implemented yet", message_id)
        except Exception as e:
            logger.error(f"Tool call error for {connection.client_id}: {e}")
            await self.send_error(connection, str(e), message_id)
    
    async def handle_resources_list(self, connection: MCPConnection, message_id: str):
        """Handle resources list request"""
        if not connection.authenticated:
            await self.send_error(connection, "Not authenticated", message_id)
            return
        
        try:
            from .resources import get_resources_list
            resources = await get_resources_list()
            
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {"resources": resources}
            }
            await connection.websocket.send(json.dumps(response))
        
        except Exception as e:
            logger.error(f"Error listing resources for {connection.client_id}: {e}")
            await self.send_error(connection, str(e), message_id)
    
    async def handle_resource_read(self, connection: MCPConnection, params: Dict[str, Any], message_id: str):
        """Handle resource read request"""
        if not connection.authenticated:
            await self.send_error(connection, "Not authenticated", message_id)
            return
        
        try:
            resource_uri = params.get("uri")
            
            from .resources import read_resource
            result = await read_resource(resource_uri)
            
            response = {
                "jsonrpc": "2.0",
                "id": message_id,
                "result": {
                    "contents": [
                        {
                            "uri": resource_uri,
                            "mimeType": "application/json",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
            await connection.websocket.send(json.dumps(response))
        
        except Exception as e:
            logger.error(f"Resource read error for {connection.client_id}: {e}")
            await self.send_error(connection, str(e), message_id)
    
    async def send_error(self, connection: MCPConnection, error_message: str, message_id: str = None):
        """Send error response to client"""
        error_response = {
            "jsonrpc": "2.0",
            "error": {
                "code": -1,
                "message": error_message,
                "data": {"timestamp": datetime.utcnow().isoformat()}
            }
        }
        
        if message_id:
            error_response["id"] = message_id
        
        try:
            await connection.websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"Failed to send error to {connection.client_id}: {e}")
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.connections)
    
    def get_authenticated_connections(self) -> int:
        """Get number of authenticated connections"""
        return len([conn for conn in self.connections.values() if conn.authenticated])
    
    async def cleanup(self):
        """Cleanup server resources"""
        logger.info("Cleaning up GTM Voyager MCP Server")
        
        # Close all connections
        for connection in self.connections.values():
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.error(f"Error closing connection {connection.client_id}: {e}")
        
        self.connections.clear()
        logger.info("GTM Voyager MCP Server cleanup completed")

# Global MCP server instance
mcp_server = GTMVoyagerMCPServer()