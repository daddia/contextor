"""
MCP Tool definitions for Contextor
"""

CONTEXTOR_TOOLS = [
    {
        "name": "fetch_page",
        "description": "Fetch a web page and convert it to markdown, storing both raw and optimized versions",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the page to fetch"
                },
                "selectors": {
                    "type": "object",
                    "description": "Optional CSS selectors for content extraction",
                    "properties": {
                        "content": {"type": "string"},
                        "title": {"type": "string"},
                        "remove": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "cache": {
                    "type": "boolean",
                    "description": "Whether to use cached content if available",
                    "default": True
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "search{source-slug}",
        "description": "Search through existing context files for relevant content",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string"
                },
                "site_filter": {
                    "type": "string",
                    "description": "Optional site slug to filter results"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_mcp_file",
        "description": "Retrieve a specific optimized MCP file",
        "input_schema": {
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": "Site slug (e.g., 'anthropic-docs')"
                },
                "page": {
                    "type": "string",
                    "description": "Page slug (e.g., 'system-prompts')"
                }
            },
            "required": ["site", "page"]
        }
    },
    {
        "name": "get_raw_markdown",
        "description": "Retrieve raw markdown content for a specific page",
        "input_schema": {
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": "Site slug"
                },
                "page": {
                    "type": "string",
                    "description": "Page slug"
                },
                "date": {
                    "type": "string",
                    "description": "Optional date (YYYY-MM-DD) for versioned content"
                }
            },
            "required": ["site", "page"]
        }
    },
    {
        "name": "list_sites",
        "description": "List all available sites and optionally their pages",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_pages": {
                    "type": "boolean",
                    "description": "Whether to include page listings for each site",
                    "default": False
                },
                "include_stats": {
                    "type": "boolean",
                    "description": "Whether to include statistics (page count, last updated)",
                    "default": False
                }
            }
        }
    },
    {
        "name": "refresh_content",
        "description": "Re-fetch and update content for specific sites or pages",
        "input_schema": {
            "type": "object",
            "properties": {
                "site": {
                    "type": "string",
                    "description": "Site slug to refresh"
                },
                "pages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific pages to refresh"
                },
                "force": {
                    "type": "boolean",
                    "description": "Force refresh even if content hasn't changed",
                    "default": False
                }
            },
            "required": ["site"]
        }
    },
    {
        "name": "optimize_markdown",
        "description": "Optimize raw markdown content for MCP consumption",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Raw markdown content to optimize"
                },
                "source_url": {
                    "type": "string",
                    "description": "Source URL of the content"
                },
                "optimization_level": {
                    "type": "string",
                    "enum": ["minimal", "standard", "aggressive"],
                    "description": "Level of optimization to apply",
                    "default": "standard"
                }
            },
            "required": ["content"]
        }
    }
]
