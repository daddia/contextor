"""
AWS Lambda handler for Contextor MCP Server
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

# Configure logging
logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Import MCP server components
from ..mcp_server import ContextorMCPServer, ContextorHandlers


# Initialize server once for Lambda container reuse
BASE_PATH = Path("/tmp/contextor")
BASE_PATH.mkdir(exist_ok=True)

# Initialize handlers
handlers = ContextorHandlers(BASE_PATH)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for MCP requests
    
    Args:
        event: Lambda event containing the request
        context: Lambda context object
    
    Returns:
        API Gateway response
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Parse request
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    headers = event.get('headers', {})
    
    # Parse body if present
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Invalid JSON in request body'})
            }
    
    try:
        # Route based on path
        if path == '/mcp/tools' and http_method == 'GET':
            # List available tools
            from ..mcp_server.tools import CONTEXTOR_TOOLS
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'tools': CONTEXTOR_TOOLS,
                    'version': '0.1.0'
                })
            }
        
        elif path.startswith('/mcp/tools/') and http_method == 'POST':
            # Execute tool
            tool_name = path.split('/')[-1]
            result = await execute_tool(tool_name, body)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        elif path == '/mcp/resources' and http_method == 'GET':
            # List available resources
            resources = list_resources()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'resources': resources})
            }
        
        elif path == '/health' and http_method == 'GET':
            # Health check
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'status': 'healthy',
                    'service': 'contextor-mcp',
                    'version': '0.1.0'
                })
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Not found'})
            }
    
    except Exception as e:
        logger.error(f"Error handling request: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a specific MCP tool
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
    
    Returns:
        Tool execution result
    """
    logger.info(f"Executing tool: {tool_name} with args: {arguments}")
    
    # Map tool names to handler methods
    tool_map = {
        'fetch_page': handlers.fetch_page,
        'search{source-slug}': handlers.search{source-slug},
        'get_mcp_file': handlers.get_mcp_file,
        'get_raw_markdown': handlers.get_raw_markdown,
        'list_sites': handlers.list_sites,
        'refresh_content': handlers.refresh_content,
        'optimize_markdown': handlers.optimize_markdown
    }
    
    if tool_name not in tool_map:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    # Execute tool
    handler = tool_map[tool_name]
    result = await handler(**arguments)
    
    return result


def list_resources() -> list:
    """
    List available resources
    
    Returns:
        List of resource descriptions
    """
    resources = []
    
    # Check for context directory
    context_dir = BASE_PATH / "{source-slug}"
    if context_dir.exists():
        resources.append({
            'uri': f's3://{os.environ.get("STORAGE_BUCKET", "contextor-storage")}/{source-slug}',
            'name': 'Context Directory',
            'description': 'Directory containing MCP context files',
            'type': 'directory'
        })
    
    # Check for raw directory
    raw_dir = BASE_PATH / "_raw"
    if raw_dir.exists():
        resources.append({
            'uri': f's3://{os.environ.get("STORAGE_BUCKET", "contextor-storage")}/_raw',
            'name': 'Raw Content Directory',
            'description': 'Directory containing raw markdown files',
            'type': 'directory'
        })
    
    return resources


# Async handler wrapper for asyncio support
def async_lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Async wrapper for Lambda handler to support async operations
    """
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Process async operations
        if event.get('path', '').startswith('/mcp/tools/') and event.get('httpMethod') == 'POST':
            body = json.loads(event.get('body', '{}'))
            tool_name = event['path'].split('/')[-1]
            
            # Run async tool execution
            result = loop.run_until_complete(execute_tool(tool_name, body))
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        else:
            # Use sync handler for non-async operations
            return lambda_handler(event, context)
    
    finally:
        loop.close()


# Environment variable configuration
if os.environ.get('ASYNC_HANDLER', 'false').lower() == 'true':
    handler = async_lambda_handler
else:
    handler = lambda_handler
