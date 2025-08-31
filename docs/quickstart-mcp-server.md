# Contextor MCP Server Quickstart Guide

This guide will help you get the Contextor MCP (Model Context Protocol) server up and running to serve content from your `sourcedocs/` directory.

## Overview

The Contextor MCP server provides a read-only interface to serve documentation and content from a `sourcedocs/` directory structure. It supports both stdio and Server-Sent Events (SSE) transports for integration with MCP clients.

## Prerequisites

- Python 3.11 or higher
- Poetry (for dependency management)
- A `sourcedocs/` directory with markdown content

## Installation

### Option 1: Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd contextor

# Install dependencies
poetry install

# Run the MCP server
poetry run contextor-server --help
```

### Option 2: Using Docker

```bash
# Build the Docker image
docker build -t contextor-mcp .

# Run with docker-compose (mounts ../sourcedocs)
docker-compose up -d

# Or run directly
docker run -p 8080:8080 -v /path/to/sourcedocs:/app/sourcedocs contextor-mcp
```

## Quick Start

### 1. Prepare Your Content

Ensure you have a `sourcedocs/` directory with your markdown content:

```
sourcedocs/
├── anthropic/
│   ├── mcp-connector.md
│   └── remote-mcp-servers.md
├── prompt-engineering/
│   └── anthropic/
│       └── system-prompts.md
└── _raw/
    └── ...
```

### 2. Start the Server

#### Stdio Transport (for MCP clients)

```bash
# Using Poetry
poetry run contextor-server --transport stdio

# Using Python module
python -m contextor.mcp_server --transport stdio

# With custom sourcedocs path
python -m contextor.mcp_server --sourcedocs-path /path/to/sourcedocs
```

#### SSE Transport (for HTTP/web access)

```bash
# Start HTTP server on localhost:8080
poetry run contextor-server --transport sse --host 0.0.0.0 --port 8080

# With custom sourcedocs path
python -m contextor.mcp_server --transport sse --sourcedocs-path /path/to/sourcedocs
```

### 3. Test the Server

Once running with SSE transport, you can test the endpoints:

```bash
# Test server health (basic check)
curl http://localhost:8080/

# Note: MCP protocol endpoints require proper MCP client integration
```

## Available Tools

The MCP server provides the following tools:

### `list_source`

List available source slugs and their content structure.

**Parameters:**
- `source_slug` (optional): Specific source to list
- `since` (optional): ISO timestamp to filter by modification time
- `include_stats` (optional): Include file count and size statistics

**Example:**
```json
{
  "source_slug": "anthropic",
  "include_stats": true
}
```

### `get_file`

Retrieve a specific file by path or slug.

**Parameters:**
- `path` OR `slug`: File identifier
  - `path`: Relative path from sourcedocs/ (e.g., "anthropic/mcp-connector.md")
  - `slug`: File slug identifier (e.g., "mcp-connector")

**Example:**
```json
{
  "path": "anthropic/mcp-connector.md"
}
```

### `search`

Search through sourcedocs content using text matching.

**Parameters:**
- `query` (required): Search query string
- `source_filter` (optional): Limit search to specific source
- `limit` (optional): Maximum results (default: 10, max: 50)
- `include_content` (optional): Include content snippets (default: true)

**Example:**
```json
{
  "query": "MCP connector",
  "source_filter": "anthropic",
  "limit": 5
}
```

### `stats`

Get statistics about the sourcedocs repository.

**Parameters:**
- `detailed` (optional): Include detailed per-source statistics

**Example:**
```json
{
  "detailed": true
}
```

## Configuration

### Environment Variables

- `SOURCEDOCS_PATH`: Path to the sourcedocs directory
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Command Line Options

```bash
python -m contextor.mcp_server --help

Options:
  --transport [stdio|sse]    Transport method (default: stdio)
  --host TEXT               Host for SSE transport (default: 0.0.0.0)
  --port INTEGER            Port for SSE transport (default: 8080)
  --sourcedocs-path PATH    Path to sourcedocs directory
  --log-level [DEBUG|INFO|WARNING|ERROR]  Logging level (default: INFO)
```

## Integration with MCP Clients

### Claude Desktop

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "contextor": {
      "command": "python",
      "args": ["-m", "contextor.mcp_server", "--sourcedocs-path", "/path/to/sourcedocs"],
      "cwd": "/path/to/contextor"
    }
  }
}
```

### Anthropic MCP Connector (HTTP)

For HTTP/SSE integration:

```bash
# Start server with SSE transport
python -m contextor.mcp_server --transport sse --host 0.0.0.0 --port 8080
```

Then connect using the MCP connector:

```json
{
  "mcp_servers": [
    {
      "type": "url",
      "url": "http://localhost:8080/sse",
      "name": "contextor"
    }
  ]
}
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run MCP server tests specifically
poetry run pytest tests/test_mcp_server.py

# Run with coverage
poetry run pytest --cov=contextor
```

### Development Server

For development, you can run the server with debug logging:

```bash
python -m contextor.mcp_server --transport sse --log-level DEBUG
```

### Docker Development

```bash
# Build and run with docker-compose
docker-compose up --build

# View logs
docker-compose logs -f contextor-mcp
```

## Troubleshooting

### Common Issues

1. **"Sourcedocs path does not exist"**
   - Ensure the sourcedocs directory exists and contains markdown files
   - Check the path specified with `--sourcedocs-path` or `SOURCEDOCS_PATH`

2. **"Permission denied" errors**
   - Ensure the server has read access to the sourcedocs directory
   - Check file permissions on the sourcedocs content

3. **"No results found" in search**
   - Verify content exists in the sourcedocs directory
   - Check that files have `.md` extension
   - Try broader search terms

4. **Connection refused (SSE transport)**
   - Ensure the server is running and the port is not blocked
   - Check firewall settings for the specified port
   - Verify the host binding (0.0.0.0 vs localhost)

### Logging

Enable debug logging for detailed troubleshooting:

```bash
python -m contextor.mcp_server --log-level DEBUG
```

### Health Checks

For Docker deployments, the container includes a basic health check:

```bash
# Check if sourcedocs directory is mounted
docker exec <container-id> test -d /app/sourcedocs && echo "OK" || echo "FAIL"
```

## Performance Considerations

- **File Caching**: The server reads files from disk on each request. For high-traffic scenarios, consider implementing caching.
- **Large Repositories**: Search performance scales with content size. Consider using `source_filter` to limit search scope.
- **Concurrent Requests**: The server handles concurrent requests asynchronously, but file I/O is still synchronous.

## Security Notes

- The server provides **read-only** access to the sourcedocs directory
- No authentication is implemented by default
- For production deployments, consider adding authentication middleware
- The server does not validate or sanitize file paths beyond basic security checks

## Next Steps

1. **Content Organization**: Organize your sourcedocs with clear source slugs
2. **Client Integration**: Set up your MCP client to connect to the server
3. **Monitoring**: Implement logging and monitoring for production use
4. **Scaling**: Consider caching and load balancing for high-traffic scenarios

For more detailed information, see the [full documentation](docs/) and [architecture documentation](docs/architecture/).
