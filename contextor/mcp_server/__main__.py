"""
Entry point for running the Contextor MCP Server as a module
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import contextor modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from contextor.mcp_server.server import main

if __name__ == "__main__":
    main()
