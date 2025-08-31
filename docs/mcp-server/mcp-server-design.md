# Contextor MCP Server Design

## Overview

This document outlines the updated Contextor architecture incorporating:
- Raw markdown storage for web content preservation
- Optimized MCP file generation from raw markdown
- Python MCP server for agent integration
- Serverless deployment architecture for cost-effective scaling

## Architecture Components

### 1. Content Processing Pipeline

```mermaid
graph LR
    A[Web Content] --> B[Raw Markdown]
    B --> C[Optimized MCP]
    C --> D[MCP Server]
    D --> E[Agent Engineers]
    
    B --> F[_raw/ Storage]
    C --> G[{source-slug}/ Storage]
```

### 2. Directory Structure

```
contextor/
├── _raw/                        # Raw markdown storage
│   ├── {site-slug}/
│   │   ├── {yyyy-mm-dd}/        # Date-versioned content
│   │   │   ├── {page-slug}.md   # Raw markdown files
│   │   │   └── metadata.json    # Extraction metadata
│   │   └── latest/              # Symlink to most recent
│
├── {source-slug}/                    # Optimized MCP files
│   ├── {site-slug}/
│   │   ├── pages/
│   │   │   └── {page-slug}.mdc  # Optimized MCP files
│   │   ├── index.json           # Site index
│   │   └── manifest.json        # MCP manifest
│
├── contextor/
│   ├── core/
│   │   ├── scraper.py           # Web scraping logic
│   │   ├── markdown_converter.py # HTML → Markdown
│   │   ├── mcp_optimizer.py     # Markdown → Optimized MCP
│   │   └── storage.py           # Storage management
│   │
│   ├── mcp_server/              # MCP Server implementation
│   │   ├── __init__.py
│   │   ├── server.py            # Main MCP server
│   │   ├── tools.py             # MCP tool definitions
│   │   └── handlers.py         # Request handlers
│   │
│   └── serverless/              # Serverless adapters
│       ├── lambda_handler.py    # AWS Lambda
│       ├── vercel_handler.py    # Vercel Functions
│       └── cloudflare_worker.py # Cloudflare Workers
```

## MCP Server Implementation

### Server Configuration

```python
# contextor/mcp_server/server.py
from mcp import Server, Tool, Resource
from mcp.server.stdio import stdio_transport
import asyncio

class ContextorMCPServer:
    def __init__(self):
        self.server = Server("contextor")
        self.setup_tools()
        
    def setup_tools(self):
        """Register available MCP tools"""
        
        # Content fetching tools
        self.server.add_tool(Tool(
            name="fetch_page",
            description="Fetch and convert a web page to markdown",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "selectors": {"type": "object"},
                    "cache": {"type": "boolean", "default": True}
                },
                "required": ["url"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="search{source-slug}",
            description="Search existing context for relevant content",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "site_filter": {"type": "string"},
                    "limit": {"type": "integer", "default": 10}
                },
                "required": ["query"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="get_mcp_file",
            description="Retrieve an optimized MCP file",
            input_schema={
                "type": "object",
                "properties": {
                    "site": {"type": "string"},
                    "page": {"type": "string"}
                },
                "required": ["site", "page"]
            }
        ))
        
        self.server.add_tool(Tool(
            name="list_sites",
            description="List available sites and their pages",
            input_schema={
                "type": "object",
                "properties": {
                    "include_pages": {"type": "boolean", "default": False}
                }
            }
        ))
        
        self.server.add_tool(Tool(
            name="refresh_content",
            description="Re-fetch and update content for a site",
            input_schema={
                "type": "object",
                "properties": {
                    "site": {"type": "string"},
                    "pages": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["site"]
            }
        ))
```

### MCP Tool Handlers

```python
# contextor/mcp_server/handlers.py
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime
from ..core import scraper, markdown_converter, mcp_optimizer

class ContextorHandlers:
    def __init__(self, base_path: Path = Path(".")):
        self.base_path = base_path
        self.raw_dir = base_path / "_raw"
        self.context_dir = base_path / "{source-slug}"
        
    async def fetch_page(self, url: str, selectors: Dict = None, cache: bool = True) -> Dict[str, Any]:
        """Fetch a web page and convert to markdown"""
        
        # Check cache first
        if cache:
            cached = self._check_cache(url)
            if cached:
                return {"status": "cached", "content": cached}
        
        # Fetch and process
        html_content = await scraper.fetch_url(url)
        markdown = markdown_converter.html_to_markdown(html_content, selectors)
        
        # Store raw markdown
        site_slug = self._extract_site_slug(url)
        page_slug = self._extract_page_slug(url)
        date_dir = datetime.now().strftime("%Y-%m-%d")
        
        raw_path = self.raw_dir / site_slug / date_dir / f"{page_slug}.md"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(markdown)
        
        # Generate optimized MCP
        mcp_content = mcp_optimizer.optimize_for{source-slug}(markdown, url)
        mcp_path = self.context_dir / site_slug / "pages" / f"{page_slug}.mdc"
        mcp_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_path.write_text(mcp_content)
        
        return {
            "status": "success",
            "raw_path": str(raw_path),
            "mcp_path": str(mcp_path),
            "content": markdown[:1000] + "..." if len(markdown) > 1000 else markdown
        }
    
    async def search{source-slug}(self, query: str, site_filter: str = None, limit: int = 10) -> List[Dict]:
        """Search through existing context files"""
        results = []
        search_dir = self.context_dir / site_filter if site_filter else self.context_dir
        
        for mcp_file in search_dir.rglob("*.mdc"):
            content = mcp_file.read_text()
            if query.lower() in content.lower():
                # Simple relevance scoring
                score = content.lower().count(query.lower())
                results.append({
                    "file": str(mcp_file.relative_to(self.context_dir)),
                    "score": score,
                    "preview": self._extract_preview(content, query)
                })
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
```

## Raw Markdown Storage

### Storage Strategy

```python
# contextor/core/storage.py
class RawMarkdownStorage:
    """Manages raw markdown storage with versioning"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        
    def store_raw(self, content: str, site: str, page: str) -> Path:
        """Store raw markdown with date versioning"""
        date = datetime.now().strftime("%Y-%m-%d")
        path = self.base_dir / site / date / f"{page}.md"
        
        # Create directory structure
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        path.write_text(content)
        
        # Update latest symlink
        latest_dir = self.base_dir / site / "latest"
        if latest_dir.exists():
            latest_dir.unlink()
        latest_dir.symlink_to(path.parent)
        
        # Store metadata
        metadata = {
            "url": f"https://{site}/{page}",
            "fetched_at": datetime.now().isoformat(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest(),
            "word_count": len(content.split()),
            "char_count": len(content)
        }
        
        metadata_path = path.parent / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, indent=2))
        
        return path
```

## MCP Optimization

### Optimization Pipeline

```python
# contextor/core/mcp_optimizer.py
class MCPOptimizer:
    """Optimizes raw markdown for MCP consumption"""
    
    def optimize_for{source-slug}(self, markdown: str, source_url: str) -> str:
        """Convert raw markdown to optimized MCP format"""
        
        # Parse markdown structure
        sections = self._parse_sections(markdown)
        
        # Optimize content
        optimized = {
            "mcp_version": "1.0",
            "source": {
                "url": source_url,
                "fetched_at": datetime.now().isoformat()
            },
            "content": self._optimize_content(sections),
            "context": self._extract{source-slug}(sections)
        }
        
        return yaml.dump(optimized, default_flow_style=False)
    
    def _optimize_content(self, sections: List[Dict]) -> Dict:
        """Optimize content for LLM consumption"""
        
        # Remove redundant content
        sections = self._remove_navigation(sections)
        sections = self._deduplicate_content(sections)
        
        # Enhance structure
        sections = self._add_section_summaries(sections)
        sections = self._extract_key_points(sections)
        
        # Compress verbose content
        sections = self._compress_examples(sections)
        
        return {
            "sections": sections,
            "summary": self._generate_summary(sections)
        }
    
    def _extract{source-slug}(self, sections: List[Dict]) -> Dict:
        """Extract contextual metadata"""
        
        return {
            "topics": self._extract_topics(sections),
            "code_languages": self._detect_languages(sections),
            "complexity": self._assess_complexity(sections),
            "prerequisites": self._identify_prerequisites(sections)
        }
```

## Serverless Deployment

### AWS Lambda Configuration

```python
# contextor/serverless/lambda_handler.py
import json
from mcp.server.sse import sse_transport
from ..mcp_server import ContextorMCPServer

server = ContextorMCPServer()

def lambda_handler(event, context):
    """AWS Lambda handler for MCP requests"""
    
    # Parse request
    body = json.loads(event.get('body', '{}'))
    
    # Handle MCP protocol
    if event['path'] == '/mcp/sse':
        # Server-Sent Events for streaming
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache'
            },
            'body': server.handle_sse(body)
        }
    
    # Handle tool invocations
    elif event['path'].startswith('/mcp/tools/'):
        tool_name = event['path'].split('/')[-1]
        result = server.invoke_tool(tool_name, body)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(result)
        }
    
    return {
        'statusCode': 404,
        'body': json.dumps({'error': 'Not found'})
    }
```

### Vercel Configuration

```python
# contextor/serverless/vercel_handler.py
from http.server import BaseHTTPRequestHandler
import json
from ..mcp_server import ContextorMCPServer

server = ContextorMCPServer()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        body = json.loads(post_data)
        
        if self.path == '/api/mcp':
            result = server.handle_request(body)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
            self.end_headers()
```

### Deployment Configuration

```yaml
# serverless.yml - AWS SAM configuration
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Timeout: 30
    MemorySize: 512
    Runtime: python3.11

Resources:
  ContextorMCPFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: contextor/
      Handler: serverless.lambda_handler.lambda_handler
      Events:
        MCPEndpoint:
          Type: Api
          Properties:
            Path: /mcp/{proxy+}
            Method: ANY
      Environment:
        Variables:
          STORAGE_BUCKET: !Ref StorageBucket
          
  StorageBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: contextor-storage
      VersioningConfiguration:
        Status: Enabled
```

```json
// vercel.json - Vercel configuration
{
  "functions": {
    "api/mcp.py": {
      "runtime": "python3.11",
      "maxDuration": 30
    }
  },
  "routes": [
    {
      "src": "/mcp/(.*)",
      "dest": "/api/mcp.py"
    }
  ]
}
```

## Cost Optimization

### Strategies for 1-5 Agent Engineers

1. **Caching Layer**
   - Use CloudFlare CDN for static MCP files
   - Redis for frequently accessed content
   - Local file cache for development

2. **On-Demand Processing**
   - Only fetch/process content when requested
   - Batch similar requests
   - Use webhooks for content updates

3. **Tiered Storage**
   - Hot: Recent/frequent content in memory
   - Warm: Last 30 days in S3 Standard
   - Cold: Archive in S3 Glacier

4. **Resource Limits**
   ```python
   # Rate limiting per agent
   RATE_LIMITS = {
       "requests_per_minute": 60,
       "concurrent_fetches": 3,
       "max_content_size_mb": 10
   }
   ```

## Usage Examples

### Local Development
```bash
# Start MCP server locally
python -m contextor.mcp_server --port 8080

# Agent connection
mcp connect http://localhost:8080
```

### Serverless Deployment
```bash
# Deploy to AWS Lambda
sam deploy --template serverless.yml

# Deploy to Vercel
vercel deploy

# Connect agents
mcp connect https://your-function.vercel.app/api/mcp
```

### Python Client Usage
```python
from mcp import Client

# Connect to Contextor MCP server
client = Client("https://contextor.example.com/mcp")

# Fetch and process a page
result = await client.call_tool("fetch_page", {
    "url": "https://docs.anthropic.com/prompt-engineering",
    "cache": True
})

# Search existing context
results = await client.call_tool("search{source-slug}", {
    "query": "chain of thought prompting",
    "limit": 5
})
```

## Security Considerations

1. **Authentication**
   - API keys for agent access
   - Rate limiting per key
   - IP allowlisting for production

2. **Content Validation**
   - Sanitize fetched HTML
   - Validate URL patterns
   - Size limits on content

3. **Data Privacy**
   - Encrypt stored content
   - GDPR compliance for cached data
   - Audit logging for access

## Monitoring & Observability

```python
# contextor/monitoring.py
import logging
from datadog import statsd

class MCPMonitor:
    def track_request(self, tool: str, duration: float):
        statsd.histogram(f'contextor.mcp.{tool}.duration', duration)
        statsd.increment(f'contextor.mcp.{tool}.count')
    
    def track_error(self, tool: str, error: str):
        logging.error(f"MCP tool {tool} failed: {error}")
        statsd.increment(f'contextor.mcp.{tool}.errors')
```

## Next Steps

1. Implement core MCP server with basic tools
2. Add authentication and rate limiting
3. Deploy to serverless platform
4. Create agent integration examples
5. Add monitoring and alerting
6. Document API and usage patterns
