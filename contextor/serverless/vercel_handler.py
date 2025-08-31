"""
Vercel Functions handler for Contextor MCP Server
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

# Import MCP server components
from ..mcp_server import SourceDocsHandlers
from ..mcp_server.tools import CONTEXTOR_TOOLS

# Configure logging
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Initialize storage path
BASE_PATH = Path("/tmp/contextor")
BASE_PATH.mkdir(exist_ok=True)

# Initialize handlers
handlers = SourceDocsHandlers(BASE_PATH)


class handler(BaseHTTPRequestHandler):
    """
    Vercel Functions handler for MCP requests
    """

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self) -> None:
        """Handle GET requests"""

        try:
            if self.path == "/api/mcp/tools":
                # List available tools
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                response = {"tools": CONTEXTOR_TOOLS, "version": "0.1.0"}
                self.wfile.write(json.dumps(response).encode())

            elif self.path == "/api/mcp/resources":
                # List resources
                resources = self._list_resources()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                self.wfile.write(json.dumps({"resources": resources}).encode())

            elif self.path == "/api/health":
                # Health check
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                response = {
                    "status": "healthy",
                    "service": "contextor-mcp",
                    "version": "0.1.0",
                    "platform": "vercel",
                }
                self.wfile.write(json.dumps(response).encode())

            else:
                self.send_error(404, "Not found")

        except Exception as e:
            logger.error(f"Error handling GET request: {e}", exc_info=True)
            self.send_error(500, str(e))

    def do_POST(self) -> None:
        """Handle POST requests"""

        try:
            # Parse request body
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                body = json.loads(post_data.decode())
            else:
                body = {}

            # Route based on path
            if self.path.startswith("/api/mcp/tools/"):
                # Execute tool
                tool_name = self.path.split("/")[-1]
                result = self._execute_tool_sync(tool_name, body)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                self.wfile.write(json.dumps(result).encode())

            elif self.path == "/api/mcp/batch":
                # Execute multiple tools in batch
                results = []
                for request in body.get("requests", []):
                    tool_name = request.get("tool")
                    arguments = request.get("arguments", {})

                    try:
                        result = self._execute_tool_sync(tool_name, arguments)
                        results.append(
                            {"tool": tool_name, "status": "success", "result": result}
                        )
                    except Exception as e:
                        results.append(
                            {"tool": tool_name, "status": "error", "error": str(e)}
                        )

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                self.wfile.write(json.dumps({"results": results}).encode())

            else:
                self.send_error(404, "Not found")

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling POST request: {e}", exc_info=True)
            self.send_error(500, str(e))

    def _execute_tool_sync(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Execute a tool synchronously

        Args:
            tool_name: Name of the tool
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        import asyncio

        # Map tool names to handler methods
        tool_map: dict[str, Any] = {
            "list_source": handlers.list_source,
            "get_file": handlers.get_file,
            "search": handlers.search,
            "stats": handlers.stats,
        }

        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Run async handler in sync context
        handler = tool_map[tool_name]

        # Create event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Execute async function
        result = loop.run_until_complete(handler(**arguments))

        return result

    def _list_resources(self) -> list[dict[str, Any]]:
        """
        List available resources

        Returns:
            List of resources
        """
        resources = []

        # Check for context directory
        context_dir = BASE_PATH / "{source-slug}"
        if context_dir.exists():
            resources.append(
                {
                    "uri": "/api/resources/context",
                    "name": "Context Directory",
                    "description": "Directory containing MCP context files",
                    "type": "directory",
                }
            )

        # Check for raw directory
        raw_dir = BASE_PATH / "_raw"
        if raw_dir.exists():
            resources.append(
                {
                    "uri": "/api/resources/raw",
                    "name": "Raw Content Directory",
                    "description": "Directory containing raw markdown files",
                    "type": "directory",
                }
            )

        return resources


# Alternative async handler for Vercel Edge Functions
async def edge_handler(request: Any) -> Any:
    """
    Vercel Edge Functions handler (async)

    Args:
        request: Vercel Edge request object

    Returns:
        Response object
    """
    from starlette.responses import JSONResponse

    try:
        # Parse request
        method = request.method
        path = request.url.path

        if method == "GET":
            if path == "/api/mcp/tools":
                return JSONResponse({"tools": CONTEXTOR_TOOLS, "version": "0.1.0"})

            elif path == "/api/health":
                return JSONResponse(
                    {
                        "status": "healthy",
                        "service": "contextor-mcp",
                        "version": "0.1.0",
                        "platform": "vercel-edge",
                    }
                )

            else:
                return JSONResponse({"error": "Not found"}, status_code=404)

        elif method == "POST":
            body = await request.json()

            if path.startswith("/api/mcp/tools/"):
                tool_name = path.split("/")[-1]

                # Execute tool
                tool_map: dict[str, Any] = {
                    "list_source": handlers.list_source,
                    "get_file": handlers.get_file,
                    "search": handlers.search,
                    "stats": handlers.stats,
                }

                if tool_name not in tool_map:
                    return JSONResponse(
                        {"error": f"Unknown tool: {tool_name}"}, status_code=400
                    )

                handler = tool_map[tool_name]
                result = await handler(**body)

                return JSONResponse(result)

            else:
                return JSONResponse({"error": "Not found"}, status_code=404)

        else:
            return JSONResponse({"error": "Method not allowed"}, status_code=405)

    except Exception as e:
        logger.error(f"Error in edge handler: {e}", exc_info=True)
        return JSONResponse(
            {"error": "Internal server error", "message": str(e)}, status_code=500
        )
