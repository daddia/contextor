"""
Contextor MCP Server - Model Context Protocol server for web content extraction and processing
"""

from .server import ContextorMCPServer
from .handlers import SourceDocsHandlers
from .tools import CONTEXTOR_TOOLS

__all__ = ['ContextorMCPServer', 'SourceDocsHandlers', 'CONTEXTOR_TOOLS']

__version__ = '0.1.0'
