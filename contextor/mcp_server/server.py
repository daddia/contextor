"""
Main MCP Server implementation for Contextor
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_transport
from mcp.types import Tool, Resource, TextContent, ImageContent

from .handlers import ContextorHandlers
from .tools import CONTEXTOR_TOOLS

logger = logging.getLogger(__name__)


class ContextorMCPServer:
    """
    MCP Server for Contextor - provides web content extraction and processing tools
    """
    
    def __init__(self, base_path: Optional[Path] = None, config: Optional[Dict] = None):
        """
        Initialize the Contextor MCP Server
        
        Args:
            base_path: Base directory for storage (defaults to current directory)
            config: Optional configuration dictionary
        """
        self.base_path = base_path or Path.cwd()
        self.config = config or {}
        
        # Initialize server with name and version
        self.server = Server("contextor")
        
        # Initialize handlers
        self.handlers = ContextorHandlers(self.base_path)
        
        # Setup tools and resources
        self._setup_tools()
        self._setup_resources()
        self._setup_handlers()
        
        logger.info(f"Contextor MCP Server initialized at {self.base_path}")
    
    def _setup_tools(self):
        """Register available MCP tools"""
        
        for tool_def in CONTEXTOR_TOOLS:
            self.server.add_tool(Tool(**tool_def))
            logger.debug(f"Registered tool: {tool_def['name']}")
    
    def _setup_resources(self):
        """Register available resources (context files, etc.)"""
        
        # Register {source-slug} directory as a resource
        context_dir = self.base_path / "{source-slug}"
        if context_dir.exists():
            self.server.add_resource(Resource(
                uri=f"file://{context_dir}",
                name="Context Directory",
                description="Directory containing MCP context files",
                mime_type="application/x-directory"
            ))
        
        # Register _raw directory as a resource
        raw_dir = self.base_path / "_raw"
        if raw_dir.exists():
            self.server.add_resource(Resource(
                uri=f"file://{raw_dir}",
                name="Raw Content Directory",
                description="Directory containing raw markdown files",
                mime_type="application/x-directory"
            ))
    
    def _setup_handlers(self):
        """Setup request handlers for tools"""
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool invocations"""
            
            logger.info(f"Tool invoked: {name} with args: {arguments}")
            
            try:
                # Route to appropriate handler
                if name == "fetch_page":
                    result = await self.handlers.fetch_page(**arguments)
                
                elif name == "search{source-slug}":
                    result = await self.handlers.search{source-slug}(**arguments)
                
                elif name == "get_mcp_file":
                    result = await self.handlers.get_mcp_file(**arguments)
                
                elif name == "list_sites":
                    result = await self.handlers.list_sites(**arguments)
                
                elif name == "refresh_content":
                    result = await self.handlers.refresh_content(**arguments)
                
                elif name == "get_raw_markdown":
                    result = await self.handlers.get_raw_markdown(**arguments)
                
                elif name == "optimize_markdown":
                    result = await self.handlers.optimize_markdown(**arguments)
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                # Format response
                if isinstance(result, dict):
                    content = self._format_dict_response(result)
                elif isinstance(result, list):
                    content = self._format_list_response(result)
                else:
                    content = str(result)
                
                return [TextContent(type="text", text=content)]
                
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    def _format_dict_response(self, data: Dict) -> str:
        """Format dictionary response as readable text"""
        import json
        return json.dumps(data, indent=2, default=str)
    
    def _format_list_response(self, data: List) -> str:
        """Format list response as readable text"""
        import json
        return json.dumps(data, indent=2, default=str)
    
    async def run(self):
        """Run the MCP server using stdio transport"""
        
        logger.info("Starting Contextor MCP Server...")
        
        async with stdio_transport(self.server):
            logger.info("Server running on stdio transport")
            # Keep server running
            await asyncio.Event().wait()
    
    async def run_sse(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the MCP server with Server-Sent Events transport for HTTP"""
        
        from mcp.server.sse import sse_transport
        
        logger.info(f"Starting Contextor MCP Server on {host}:{port}...")
        
        async with sse_transport(self.server, host=host, port=port):
            logger.info(f"Server running on http://{host}:{port}")
            # Keep server running
            await asyncio.Event().wait()


def main():
    """Main entry point for running the server"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Contextor MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport method (stdio or sse)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for SSE transport"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE transport"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="Base path for storage"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = ContextorMCPServer(base_path=args.base_path)
    
    if args.transport == "stdio":
        asyncio.run(server.run())
    else:
        asyncio.run(server.run_sse(host=args.host, port=args.port))


if __name__ == "__main__":
    main()
