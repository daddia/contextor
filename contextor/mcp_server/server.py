"""
Main MCP-compatible Server implementation for Contextor using FastAPI
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from .handlers import SourceDocsHandlers

logger = logging.getLogger(__name__)


class ContextorMCPServer:
    """
    MCP-compatible Server for Contextor - serves content from sourcedocs directory
    """
    
    def __init__(self, sourcedocs_path: Path):
        """
        Initialize the Contextor MCP Server
        
        Args:
            sourcedocs_path: Path to the sourcedocs directory
        """
        self.sourcedocs_path = sourcedocs_path.resolve()
        
        if not self.sourcedocs_path.exists():
            raise ValueError(f"Sourcedocs path does not exist: {self.sourcedocs_path}")
        
        # Initialize handlers
        self.handlers = SourceDocsHandlers(self.sourcedocs_path)
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Contextor MCP Server",
            description="Model Context Protocol compatible server for serving sourcedocs content",
            version="0.1.0"
        )
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Contextor MCP Server initialized with sourcedocs: {self.sourcedocs_path}")
    
    def _setup_routes(self):
        """Setup FastAPI routes for MCP tools"""
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/tools")
        async def list_tools():
            """List available MCP tools"""
            from .tools import CONTEXTOR_TOOLS
            return {"tools": CONTEXTOR_TOOLS}
        
        @self.app.post("/tools/list_source")
        async def list_source_tool(request: Dict[str, Any]):
            """List source tool endpoint"""
            try:
                result = await self.handlers.list_source(**request)
                return result
            except Exception as e:
                logger.error(f"Error in list_source: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/get_file")
        async def get_file_tool(request: Dict[str, Any]):
            """Get file tool endpoint"""
            try:
                result = await self.handlers.get_file(**request)
                if result.get("status") == "not_found":
                    raise HTTPException(status_code=404, detail=result.get("error"))
                return result
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in get_file: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/search")
        async def search_tool(request: Dict[str, Any]):
            """Search tool endpoint"""
            try:
                result = await self.handlers.search(**request)
                return {"results": result}
            except Exception as e:
                logger.error(f"Error in search: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/tools/stats")
        async def stats_tool(request: Dict[str, Any]):
            """Stats tool endpoint"""
            try:
                result = await self.handlers.stats(**request)
                return result
            except Exception as e:
                logger.error(f"Error in stats: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        # REST-style endpoints for easier HTTP access
        @self.app.get("/sources")
        async def list_sources(
            source_slug: Optional[str] = None,
            since: Optional[str] = None,
            include_stats: bool = False
        ):
            """REST endpoint to list sources"""
            result = await self.handlers.list_source(
                source_slug=source_slug,
                since=since,
                include_stats=include_stats
            )
            return result
        
        @self.app.get("/sources/{source_slug}")
        async def get_source_details(source_slug: str, include_stats: bool = False):
            """REST endpoint to get specific source details"""
            result = await self.handlers.list_source(
                source_slug=source_slug,
                include_stats=include_stats
            )
            if result.get("status") == "not_found":
                raise HTTPException(status_code=404, detail=result.get("error"))
            return result
        
        @self.app.get("/files")
        async def get_file_by_path(path: Optional[str] = None, slug: Optional[str] = None):
            """REST endpoint to get file by path or slug"""
            if not path and not slug:
                raise HTTPException(status_code=400, detail="Either path or slug must be provided")
            
            result = await self.handlers.get_file(path=path, slug=slug)
            if result.get("status") == "not_found":
                raise HTTPException(status_code=404, detail=result.get("error"))
            return result
        
        @self.app.get("/search")
        async def search_content(
            query: str,
            source_filter: Optional[str] = None,
            limit: int = 10,
            include_content: bool = True
        ):
            """REST endpoint to search content"""
            result = await self.handlers.search(
                query=query,
                source_filter=source_filter,
                limit=limit,
                include_content=include_content
            )
            return {"results": result}
        
        @self.app.get("/stats")
        async def get_stats(detailed: bool = False):
            """REST endpoint to get repository statistics"""
            result = await self.handlers.stats(detailed=detailed)
            return result
        
        # Server-Sent Events endpoint for real-time updates
        @self.app.get("/stream")
        async def stream_updates(request: Request):
            """SSE endpoint for real-time updates"""
            
            async def event_generator():
                last_check = datetime.now()
                
                while True:
                    if await request.is_disconnected():
                        break
                    
                    try:
                        # Check for any updates since last check
                        current_time = datetime.now()
                        since_iso = last_check.isoformat()
                        
                        # Get updated sources
                        updates = await self.handlers.list_source(since=since_iso, include_stats=True)
                        
                        if updates.get("sources"):
                            # Send update event
                            event_data = {
                                "type": "sources_updated",
                                "timestamp": current_time.isoformat(),
                                "data": updates
                            }
                            
                            yield {
                                "event": "update",
                                "data": json.dumps(event_data)
                            }
                        
                        last_check = current_time
                        await asyncio.sleep(30)  # Check every 30 seconds
                        
                    except Exception as e:
                        logger.error(f"Error in SSE stream: {e}")
                        yield {
                            "event": "error",
                            "data": json.dumps({"error": str(e)})
                        }
                        await asyncio.sleep(5)
            
            return EventSourceResponse(event_generator())
    
    def get_app(self):
        """Get the FastAPI app instance"""
        return self.app


def create_app(sourcedocs_path: Path) -> FastAPI:
    """Factory function to create FastAPI app"""
    server = ContextorMCPServer(sourcedocs_path)
    return server.get_app()


def main():
    """Main entry point for running the server"""
    
    import argparse
    import os
    import uvicorn
    
    parser = argparse.ArgumentParser(description="Contextor MCP Server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to bind to"
    )
    parser.add_argument(
        "--sourcedocs-path",
        type=Path,
        help="Path to sourcedocs directory (defaults to ./sourcedocs or env var SOURCEDOCS_PATH)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Determine sourcedocs path
    if args.sourcedocs_path:
        sourcedocs_path = args.sourcedocs_path
    elif os.getenv("SOURCEDOCS_PATH"):
        sourcedocs_path = Path(os.getenv("SOURCEDOCS_PATH"))
    else:
        # Default to ./sourcedocs relative to current working directory
        sourcedocs_path = Path.cwd() / "sourcedocs"
    
    logger.info(f"Using sourcedocs path: {sourcedocs_path}")
    
    # Create app
    try:
        app = create_app(sourcedocs_path)
        
        # Run server
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            log_level=args.log_level.lower(),
            reload=args.reload
        )
    
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        exit(1)


if __name__ == "__main__":
    main()