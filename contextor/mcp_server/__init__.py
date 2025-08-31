"""
Contextor MCP Server - Model Context Protocol server for web content extraction and processing
"""

from .server import ContextorMCPServer
from .handlers import ContextorHandlers
from .tools import CONTEXTOR_TOOLS

__all__ = ['ContextorMCPServer', 'ContextorHandlers', 'CONTEXTOR_TOOLS']

__version__ = '0.1.0'
