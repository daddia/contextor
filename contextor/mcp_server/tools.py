"""
MCP Tool definitions for Contextor - Updated for sourcedocs serving
"""

CONTEXTOR_TOOLS = [
    {
        "name": "list_source",
        "description": "List available source slugs and their content structure",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_slug": {
                    "type": "string",
                    "description": "Optional source slug to get detailed listing for (e.g., 'anthropic', 'prompt-engineering')"
                },
                "since": {
                    "type": "string",
                    "description": "Optional ISO timestamp to filter content updated since this date"
                },
                "include_stats": {
                    "type": "boolean",
                    "description": "Whether to include file count and size statistics",
                    "default": False
                }
            }
        }
    },
    {
        "name": "get_file",
        "description": "Retrieve a specific file by path or slug from sourcedocs",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to sourcedocs/ (e.g., 'anthropic/mcp-connector.md')"
                },
                "slug": {
                    "type": "string",
                    "description": "Alternative: file slug identifier"
                }
            },
            "oneOf": [
                {"required": ["path"]},
                {"required": ["slug"]}
            ]
        }
    },
    {
        "name": "search",
        "description": "Search through sourcedocs content using text matching",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string"
                },
                "source_filter": {
                    "type": "string",
                    "description": "Optional source slug to limit search scope"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Whether to include content snippets in results",
                    "default": True
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "stats",
        "description": "Get statistics about the sourcedocs repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "detailed": {
                    "type": "boolean",
                    "description": "Whether to include detailed per-source statistics",
                    "default": False
                }
            }
        }
    }
]