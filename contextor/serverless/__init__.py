"""
Serverless deployment handlers for Contextor MCP Server
"""

from .lambda_handler import async_lambda_handler, lambda_handler
from .vercel_handler import edge_handler as vercel_edge_handler
from .vercel_handler import handler as vercel_handler

__all__ = [
    "lambda_handler",
    "async_lambda_handler",
    "vercel_handler",
    "vercel_edge_handler",
]
