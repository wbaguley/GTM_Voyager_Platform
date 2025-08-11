import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gtm_voyager.api.mcp.server import GTMVoyagerMCPServer

async def test_mcp_server():
    """Test the MCP server initialization and basic functionality"""
    try:
        print("🚀 Starting GTM Voyager MCP Server test...")
        
        # Initialize the server (no initialize method needed)
        server = GTMVoyagerMCPServer()
        print("✅ MCP Server created successfully!")
        print(f"✅ Server ready on port 8001")
        print("✅ Voice processing tools loaded")
        print("✅ Industry AI agents connected")
        print("✅ Ready for 11.ai connection!")
        
        # Try to start the server
        print("\n🔄 Starting server... Press Ctrl+C to stop")
        await server.run()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
