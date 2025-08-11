"""
GTM Voyager MCP Server
Main WebSocket server for Model Context Protocol integration with 11.ai
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Any, Optional, List
from datetime import datetime
import traceback

from .tools import get_all_mcp_tools, execute_tool
from .resources import get_all_mcp_resources, get_resource
from .auth import MCPAuthenticator
from ...config import mcp_config

logger = logging.getLogger(__name__)

class GTMVoyagerMCPServer:
    """Main MCP server for GTM Voyager Platform"""
    
    def __init__(self):
        self.tools: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}
        self.authenticator = MCPAuthenticator()
        self.connected_clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.server = None
        
    async def initialize(self):
        """Initialize the MCP server with tools and resources"""
        try:
            # Load all available tools
            tools_list = await get_all_mcp_tools()
            self.tools = {tool["name"]: tool for tool in tools_list}
            logger.info(f"Loaded {len(self.tools)} MCP tools")
            
            # Load all available resources
            resources_list = await get_all_mcp_resources()
            self.resources = {resource["uri"]: resource for resource in resources_list}
            logger.info(f"Loaded {len(self.resources)} MCP resources")
            
            logger.info("GTM Voyager MCP Server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            logger.error(traceback.format_exc())
            raise
    
    async def handle_client_connection(self, websocket, path):
        """Handle new client connections"""
        client_id = f"client_{len(self.connected_clients)}"
        self.connected_clients[client_id] = websocket
        logger.info(f"New MCP client connected: {client_id}")
        
        try:
            async for message in websocket:
                await self.handle_message(client_id, websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"MCP client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
    
    async def handle_message(self, client_id: str, websocket, message: str):
        """Handle incoming MCP messages"""
        try:
            data = json.loads(message)
            method = data.get("method")
            params = data.get("params", {})
            message_id = data.get("id")
            
            logger.debug(f"Received MCP message from {client_id}: {method}")
            
            # Route message to appropriate handler
            if method == "initialize":
                response = await self.handle_initialize(params)
            elif method == "tools/list":
                response = await self.handle_tools_list(params)
            elif method == "tools/call":
                response = await self.handle_tool_call(params)
            elif method == "resources/list":
                response = await self.handle_resources_list(params)
            elif method == "resources/read":
                response = await self.handle_resource_read(params)
            elif method == "ping":
                response = {"result": {"message": "pong"}}
            else:
                response = {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            # Add message ID to response
            if message_id:
                response["id"] = message_id
            
            # Send response
            await websocket.send(json.dumps(response))
            
        except json.JSONDecodeError:
            error_response = {
                "error": {
                    "code": -32700,
                    "message": "Parse error: Invalid JSON"
                }
            }
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            error_response = {
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            await websocket.send(json.dumps(error_response))
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization request"""
        return {
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    },
                    "resources": {
                        "subscribe": True,
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "GTM Voyager Platform",
                    "version": "1.0.0",
                    "description": "Voice-first business automation platform with industry-specific AI agents"
                }
            }
        }
    
    async def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools list request"""
        tools_list = list(self.tools.values())
        return {
            "result": {
                "tools": tools_list
            }
        }
    
    async def handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Tool not found: {tool_name}"
                }
            }
        
        try:
            result = await execute_tool(tool_name, arguments)
            return {
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": f"Tool execution failed: {str(e)}"
                }
            }
    
    async def handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources list request"""
        resources_list = list(self.resources.values())
        return {
            "result": {
                "resources": resources_list
            }
        }
    
    async def handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read request"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            return {
                "error": {
                    "code": -32602,
                    "message": f"Resource not found: {uri}"
                }
            }
        
        try:
            content = await get_resource(uri)
            return {
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/json",
                            "text": json.dumps(content, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": f"Resource read failed: {str(e)}"
                }
            }
    
    async def start_server(self, host: str = "localhost", port: int = None):
        """Start the WebSocket server"""
        if port is None:
            port = mcp_config.MCP_SERVER_PORT
        
        try:
            await self.initialize()
            
            self.server = await websockets.serve(
                self.handle_client_connection,
                host,
                port,
                ping_interval=30,
                ping_timeout=10
            )
            
            logger.info(f"GTM Voyager MCP Server started on {host}:{port}")
            logger.info(f"Available tools: {list(self.tools.keys())}")
            logger.info(f"Available resources: {list(self.resources.keys())}")
            
            return self.server
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            raise
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("GTM Voyager MCP Server stopped")

# Global server instance
mcp_server = GTMVoyagerMCPServer()

async def initialize():
    """Initialize the global MCP server instance"""
    await mcp_server.initialize()

async def start_server(host: str = "localhost", port: int = None):
    """Start the global MCP server"""
    return await mcp_server.start_server(host, port)

async def stop_server():
    """Stop the global MCP server"""
    await mcp_server.stop_server()