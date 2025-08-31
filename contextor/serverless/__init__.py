"""
Serverless deployment handlers for Contextor MCP Server
"""

from .lambda_handler import lambda_handler, async_lambda_handler
from .vercel_handler import handler as vercel_handler, edge_handler as vercel_edge_handler

__all__ = [
    'lambda_handler',
    'async_lambda_handler', 
    'vercel_handler',
    'vercel_edge_handler'
]
