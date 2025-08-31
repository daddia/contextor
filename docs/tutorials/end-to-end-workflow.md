---
title: "Complete Workflow Tutorial"
canonical_id: "DOC-TUT-001"
version: "1.0.0"
updated: "2025-01-12"
owner: "Contextor Team"
status: "approved"
tags: ["tutorial", "workflow", "end-to-end"]
source_url: "https://github.com/daddia/contextor/docs/tutorials/end-to-end-workflow.md"
---

# Complete Workflow Tutorial [ID: DOC-TUT-001]

This comprehensive tutorial walks you through the complete Contextor workflow, from setup to MCP server deployment and agent integration.

## Summary

- Set up Contextor development environment with Poetry
- Process Next.js documentation as a practical example
- Configure and run intelligence analysis for content insights
- Deploy MCP server for agent integration
- Integrate processed content with AI workflows
- Establish automated update pipelines

## Prerequisites

Before starting this tutorial, ensure you have:

- Python 3.11 or higher installed
- Git for repository management
- Basic familiarity with command line operations
- Understanding of Markdown and documentation formats

## Tutorial Overview

**Estimated Time**: 45 minutes

**Learning Objectives**:
- Understand the complete Contextor workflow
- Process real documentation into MCP format
- Set up intelligence analysis
- Deploy and use MCP server
- Integrate with AI agent workflows

## Step 1: Environment Setup

### Install Contextor

```bash
# Clone the repository
git clone https://github.com/daddia/contextor.git
cd contextor

# Install with Poetry (recommended)
poetry install

# Install with intelligence features
poetry install --extras intelligence

# Verify installation
poetry run contextor --version
```

### Prepare Workspace

```bash
# Create workspace directories
mkdir -p ../workspace/{vendor,sourcedocs}
cd ../workspace

# Clone target documentation (Next.js example)
git clone https://github.com/vercel/next.js.git vendor/nextjs
cd vendor/nextjs
git checkout main  # Use specific commit for reproducibility

# Return to contextor directory
cd ../../contextor
```

## Step 2: Basic Documentation Processing

### List Available Project Configurations

```bash
# See what project configurations are available
poetry run contextor list-projects
```

**Expected Output:**
```
Available project configurations:
  nextjs: Next.js React framework (vercel/next.js)
  react: React library (facebook/react)
  tailwindcss: Tailwind CSS framework (tailwindlabs/tailwindcss)
  vite: Vite build tool (vitejs/vite)
  vscode: Visual Studio Code (microsoft/vscode)
```

### Process Next.js Documentation

```bash
# Process using project configuration (recommended)
poetry run contextor optimize \
  --src ../workspace/vendor/nextjs/docs \
  --out ../workspace/sourcedocs/nextjs \
  --project-config nextjs

# Alternative: Manual configuration
poetry run contextor optimize \
  --src ../workspace/vendor/nextjs/docs \
  --out ../workspace/sourcedocs/nextjs \
  --repo vercel/next.js \
  --ref main \
  --topics "framework,react,javascript" \
  --profile balanced
```

**Expected Output:**
```
Processing documentation from ../workspace/vendor/nextjs/docs
Repository: vercel/next.js (ref: main)
Profile: balanced
Topics: framework, react, javascript

Discovered 127 files (98 .md, 29 .mdx)
Processed: 127 files
Written: 127 .mdc files
Skipped: 0 files
Errors: 0 files

Output directory: ../workspace/sourcedocs/nextjs
Index file: ../workspace/sourcedocs/nextjs/index.jsonl
```

### Verify Output Structure

```bash
# Check generated structure
ls -la ../workspace/sourcedocs/nextjs/

# Expected structure:
# pages/           - .mdc files
# index.jsonl      - Document index
# metrics.json     - Processing metrics (if requested)
```

### Examine Generated MCP Files

```bash
# Look at a sample .mdc file
head -50 ../workspace/sourcedocs/nextjs/pages/getting-started.mdc
```

**Expected MCP File Structure:**
```json
{
  "source": {
    "url": "https://github.com/vercel/next.js/blob/main/docs/getting-started.md",
    "canonical_url": "https://nextjs.org/docs/getting-started",
    "repository": "vercel/next.js",
    "ref": "main",
    "path": "docs/getting-started.md",
    "last_modified": "2025-01-12T10:30:00Z"
  },
  "metadata": {
    "title": "Getting Started",
    "slug": "getting-started",
    "topics": ["framework", "react", "javascript", "setup"],
    "content_hash": "sha256:abc123...",
    "processing": {
      "profile": "balanced",
      "transforms_applied": ["mdx_cleanup", "heading_normalization", "link_fixing"],
      "token_count": 1250,
      "estimated_cost": 0.0025
    }
  },
  "content": {
    "title": "Getting Started",
    "body": "# Getting Started\n\nNext.js is a React framework..."
  }
}
```

## Step 3: Intelligence Analysis

### Enable Intelligence Features

```bash
# Ensure intelligence dependencies are installed
poetry install --extras intelligence

# Create intelligence configuration (optional)
cat > config/intelligence.yaml << EOF
topic_extraction:
  min_topic_frequency: 3
  max_topics_per_document: 10

cross_linking:
  max_related_documents: 5
  topic_overlap_threshold: 0.3

quality_scoring:
  completeness_weight: 0.4
  freshness_weight: 0.3
  clarity_weight: 0.3

duplicate_detection:
  similarity_threshold: 0.8
EOF
```

### Run Intelligence Analysis

```bash
# Run all intelligence features
poetry run contextor intelligence \
  --source-dir ../workspace/sourcedocs/nextjs \
  --features topic-extraction,cross-linking,quality-scoring,duplicate-detection \
  --metrics-output intelligence-metrics.json
```

**Expected Output:**
```
Starting intelligence analysis
Source directory: ../workspace/sourcedocs/nextjs
Features: topic-extraction, cross-linking, quality-scoring, duplicate-detection

Phase 1: Individual document analysis
Processed: 127 documents
Updated: 127 documents
Skipped: 0 documents
Errors: 0 documents

Phase 2: Cross-document analysis
Cross-links identified: 245
Topic clusters: 12
Quality scores calculated: 127

Intelligence index written to: ../workspace/sourcedocs/nextjs/intelligence.jsonl
```

### Examine Intelligence Results

```bash
# View intelligence index
head -10 ../workspace/sourcedocs/nextjs/intelligence.jsonl

# Check metrics
cat intelligence-metrics.json | jq '.topic_extraction'
```

**Sample Intelligence Data:**
```json
{
  "file_path": "pages/routing.mdc",
  "intelligence": {
    "extracted_topics": ["routing", "navigation", "pages", "dynamic-routes"],
    "quality_score": {
      "completeness": 0.85,
      "freshness": 0.90,
      "clarity": 0.88,
      "overall": 0.87
    },
    "related_documents": [
      {
        "path": "pages/api-routes.mdc",
        "relevance": 0.75,
        "relationship": "complementary"
      }
    ],
    "cross_links": [
      {
        "target": "pages/dynamic-routing.mdc",
        "anchor_text": "dynamic routing",
        "confidence": 0.92
      }
    ]
  }
}
```

## Step 4: MCP Server Deployment

### Local MCP Server

```bash
# Start MCP server with stdio transport
poetry run contextor-server --transport=stdio

# Or start with HTTP transport for testing
poetry run contextor-server \
  --transport=sse \
  --host=0.0.0.0 \
  --port=8080 \
  --sourcedocs-path=../workspace/sourcedocs
```

### Test MCP Server

```bash
# In another terminal, test the server
curl http://localhost:8080/health

# List available tools
curl http://localhost:8080/tools

# Test list_source tool
curl -X POST http://localhost:8080/tools/list_source \
  -H "Content-Type: application/json" \
  -d '{"include_stats": true}'
```

**Expected Response:**
```json
{
  "sources": [
    {
      "source_slug": "nextjs",
      "title": "Next.js Documentation",
      "file_count": 127,
      "total_size": 2048576,
      "last_updated": "2025-01-12T10:30:00Z"
    }
  ],
  "total_sources": 1,
  "total_files": 127
}
```

### Test Content Retrieval

```bash
# Get a specific file
curl -X POST http://localhost:8080/tools/get_file \
  -H "Content-Type: application/json" \
  -d '{"path": "nextjs/pages/getting-started.mdc"}'

# Search content
curl -X POST http://localhost:8080/tools/search \
  -H "Content-Type: application/json" \
  -d '{"query": "routing", "source_filter": "nextjs", "limit": 5}'
```

## Step 5: Agent Integration

### Claude Desktop Integration

Create MCP server configuration for Claude Desktop:

```json
{
  "mcpServers": {
    "contextor": {
      "command": "poetry",
      "args": ["run", "contextor-server", "--transport=stdio"],
      "cwd": "/path/to/contextor",
      "env": {
        "SOURCEDOCS_PATH": "/path/to/workspace/sourcedocs"
      }
    }
  }
}
```

### Python Agent Integration

```python
# agent_integration.py
import json
import subprocess
from pathlib import Path

class ContextorAgent:
    def __init__(self, sourcedocs_path: str):
        self.sourcedocs_path = Path(sourcedocs_path)

    def search_documentation(self, query: str, source_filter: str = None) -> list:
        """Search processed documentation"""
        # This would integrate with MCP server
        # For demo, we'll read files directly
        results = []

        for source_dir in self.sourcedocs_path.iterdir():
            if source_filter and source_dir.name != source_filter:
                continue

            pages_dir = source_dir / "pages"
            if pages_dir.exists():
                for mdc_file in pages_dir.glob("*.mdc"):
                    with open(mdc_file) as f:
                        mdc_data = json.load(f)
                        content = mdc_data.get("content", {}).get("body", "")
                        if query.lower() in content.lower():
                            results.append({
                                "file": str(mdc_file),
                                "title": mdc_data.get("content", {}).get("title"),
                                "source": mdc_data.get("source", {}).get("canonical_url"),
                                "topics": mdc_data.get("metadata", {}).get("topics", [])
                            })

        return results

    def get_related_content(self, topic: str) -> list:
        """Get content related to a specific topic"""
        related = []

        for source_dir in self.sourcedocs_path.iterdir():
            intelligence_file = source_dir / "intelligence.jsonl"
            if intelligence_file.exists():
                with open(intelligence_file) as f:
                    for line in f:
                        doc_intel = json.loads(line)
                        extracted_topics = doc_intel.get("intelligence", {}).get("extracted_topics", [])
                        if topic in extracted_topics:
                            related.append(doc_intel)

        return related

# Usage example
agent = ContextorAgent("../workspace/sourcedocs")

# Search for routing documentation
routing_docs = agent.search_documentation("routing", "nextjs")
print(f"Found {len(routing_docs)} documents about routing")

# Get content related to React hooks
hooks_content = agent.get_related_content("hooks")
print(f"Found {len(hooks_content)} documents about hooks")
```

## Step 6: Automation Setup

### GitHub Actions Workflow

Create `.github/workflows/update-documentation.yml`:

```yaml
name: Update Documentation Context

on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday at 6 AM
  workflow_dispatch:
  push:
    paths:
      - 'config/projects/*.json'

jobs:
  update-context:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        project: [nextjs, react, tailwindcss, vite]

    steps:
      - name: Checkout Contextor
        uses: actions/checkout@v4
        with:
          path: contextor

      - name: Checkout Sourcedocs
        uses: actions/checkout@v4
        with:
          repository: your-org/sourcedocs
          token: ${{ secrets.SOURCEDOCS_TOKEN }}
          path: sourcedocs

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install Dependencies
        run: |
          cd contextor
          poetry install --extras intelligence

      - name: Clone Source Documentation
        run: |
          mkdir -p vendor
          case "${{ matrix.project }}" in
            nextjs)
              git clone --depth 1 https://github.com/vercel/next.js.git vendor/nextjs
              ;;
            react)
              git clone --depth 1 https://github.com/facebook/react.git vendor/react
              ;;
            tailwindcss)
              git clone --depth 1 https://github.com/tailwindlabs/tailwindcss.git vendor/tailwindcss
              ;;
            vite)
              git clone --depth 1 https://github.com/vitejs/vite.git vendor/vite
              ;;
          esac

      - name: Process Documentation
        run: |
          cd contextor
          poetry run contextor optimize \
            --src "../vendor/${{ matrix.project }}/docs" \
            --out "../sourcedocs/${{ matrix.project }}" \
            --project-config "${{ matrix.project }}" \
            --metrics-output "../sourcedocs/${{ matrix.project }}/metrics.json"

      - name: Run Intelligence Analysis
        run: |
          cd contextor
          poetry run contextor intelligence \
            --source-dir "../sourcedocs/${{ matrix.project }}" \
            --features topic-extraction,cross-linking,quality-scoring,duplicate-detection \
            --metrics-output "../sourcedocs/${{ matrix.project }}/intelligence-metrics.json"

      - name: Commit Changes
        run: |
          cd sourcedocs
          git config --local user.name "GitHub Actions"
          git config --local user.email "action@github.com"
          git add .
          git commit -m "Update ${{ matrix.project }} context: $(date -I)" || exit 0
          git push
```

### Local Automation Script

Create `scripts/update-context.sh`:

```bash
#!/bin/bash
# update-context.sh - Local automation script

set -e

PROJECTS=("nextjs" "react" "tailwindcss" "vite")
WORKSPACE_DIR="../workspace"
VENDOR_DIR="$WORKSPACE_DIR/vendor"
SOURCEDOCS_DIR="$WORKSPACE_DIR/sourcedocs"

echo "Starting Contextor documentation update..."

# Ensure directories exist
mkdir -p "$VENDOR_DIR" "$SOURCEDOCS_DIR"

for project in "${PROJECTS[@]}"; do
    echo ""
    echo "=== Processing $project ==="

    # Update source repository
    if [ -d "$VENDOR_DIR/$project" ]; then
        echo "Updating existing $project repository..."
        cd "$VENDOR_DIR/$project"
        git pull origin main
        cd - > /dev/null
    else
        echo "Cloning $project repository..."
        case "$project" in
            nextjs)
                git clone https://github.com/vercel/next.js.git "$VENDOR_DIR/$project"
                ;;
            react)
                git clone https://github.com/facebook/react.git "$VENDOR_DIR/$project"
                ;;
            tailwindcss)
                git clone https://github.com/tailwindlabs/tailwindcss.git "$VENDOR_DIR/$project"
                ;;
            vite)
                git clone https://github.com/vitejs/vite.git "$VENDOR_DIR/$project"
                ;;
        esac
    fi

    # Process documentation
    echo "Processing $project documentation..."
    poetry run contextor optimize \
        --src "$VENDOR_DIR/$project/docs" \
        --out "$SOURCEDOCS_DIR/$project" \
        --project-config "$project" \
        --metrics-output "$SOURCEDOCS_DIR/$project/metrics.json"

    # Run intelligence analysis
    echo "Running intelligence analysis for $project..."
    poetry run contextor intelligence \
        --source-dir "$SOURCEDOCS_DIR/$project" \
        --features topic-extraction,cross-linking,quality-scoring,duplicate-detection \
        --metrics-output "$SOURCEDOCS_DIR/$project/intelligence-metrics.json"

    echo "✓ $project processing completed"
done

echo ""
echo "All projects processed successfully!"
echo "Results available in: $SOURCEDOCS_DIR"
```

Make the script executable:

```bash
chmod +x scripts/update-context.sh
```

## Step 7: MCP Server Deployment

### Local Development Server

```bash
# Start server with stdio transport (for Claude Desktop)
poetry run contextor-server --transport=stdio

# Start server with HTTP transport (for testing)
poetry run contextor-server \
  --transport=sse \
  --host=0.0.0.0 \
  --port=8080 \
  --sourcedocs-path=../workspace/sourcedocs
```

### Docker Deployment

Create `Dockerfile.mcp`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY contextor/ ./contextor/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main

# Copy sourcedocs (or mount as volume)
COPY sourcedocs/ ./sourcedocs/

# Expose port
EXPOSE 8080

# Start server
CMD ["poetry", "run", "contextor-server", "--transport=sse", "--host=0.0.0.0", "--port=8080"]
```

Build and run:

```bash
# Build Docker image
docker build -f Dockerfile.mcp -t contextor-mcp .

# Run with volume mount for sourcedocs
docker run -p 8080:8080 \
  -v /path/to/sourcedocs:/app/sourcedocs:ro \
  contextor-mcp
```

### Production Deployment

Using docker-compose for production:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  contextor-mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    ports:
      - "8080:8080"
    volumes:
      - ./sourcedocs:/app/sourcedocs:ro
      - ./logs:/app/logs
    environment:
      - CONTEXTOR_LOG_LEVEL=INFO
      - SOURCEDOCS_PATH=/app/sourcedocs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Deploy:

```bash
# Deploy production server
docker-compose -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Step 8: Advanced Integration

### Custom Agent Workflow

```python
# advanced_agent.py
import json
import requests
from pathlib import Path
from typing import List, Dict, Any

class AdvancedContextorAgent:
    def __init__(self, mcp_server_url: str = "http://localhost:8080"):
        self.server_url = mcp_server_url

    def get_contextual_documentation(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get relevant documentation for a query with intelligence insights"""

        # Search for relevant content
        search_response = requests.post(f"{self.server_url}/tools/search", json={
            "query": query,
            "limit": max_results,
            "include_content": True
        })

        results = search_response.json().get("results", [])

        # Enrich with intelligence data
        enriched_results = []
        for result in results:
            # Get full file content
            file_response = requests.post(f"{self.server_url}/tools/get_file", json={
                "path": result["path"]
            })

            if file_response.status_code == 200:
                file_data = file_response.json()

                # Add intelligence insights
                intelligence = file_data.get("intelligence", {})

                enriched_results.append({
                    "content": file_data,
                    "relevance_score": result.get("score", 0),
                    "topics": intelligence.get("extracted_topics", []),
                    "quality_score": intelligence.get("quality_score", {}),
                    "related_docs": intelligence.get("related_documents", [])
                })

        return enriched_results

    def build_contextual_prompt(self, user_query: str, context_limit: int = 5) -> str:
        """Build a contextual prompt with relevant documentation"""

        # Get relevant documentation
        docs = self.get_contextual_documentation(user_query, context_limit)

        # Build prompt with context
        prompt_parts = [
            f"User Query: {user_query}",
            "",
            "Relevant Documentation Context:",
            ""
        ]

        for i, doc in enumerate(docs, 1):
            content = doc["content"]["content"]["body"][:1000]  # Truncate for demo
            quality = doc["quality_score"].get("overall", 0)
            topics = ", ".join(doc["topics"][:3])

            prompt_parts.extend([
                f"## Document {i}: {doc['content']['content']['title']}",
                f"Source: {doc['content']['source']['canonical_url']}",
                f"Quality Score: {quality:.2f} | Topics: {topics}",
                f"Content: {content}...",
                ""
            ])

        return "\n".join(prompt_parts)

# Usage example
agent = AdvancedContextorAgent()

# Get contextual documentation for a query
context_prompt = agent.build_contextual_prompt("How do I set up dynamic routing in Next.js?")
print(context_prompt)
```

### Monitoring and Metrics

```python
# monitoring.py
import json
import requests
from datetime import datetime

def collect_usage_metrics(server_url: str = "http://localhost:8080"):
    """Collect usage metrics from MCP server"""

    # Get server stats
    stats_response = requests.post(f"{server_url}/tools/stats", json={
        "detailed": True
    })

    if stats_response.status_code == 200:
        stats = stats_response.json()

        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "server_stats": stats,
            "health_check": requests.get(f"{server_url}/health").json()
        }

        # Save metrics
        with open(f"metrics-{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
            json.dump(metrics, f, indent=2)

        return metrics

    return None

# Collect daily metrics
metrics = collect_usage_metrics()
if metrics:
    print(f"Collected metrics for {len(metrics['server_stats']['sources'])} sources")
```

## Verification and Testing

### Validate Complete Workflow

```bash
# 1. Verify documentation processing
ls -la ../workspace/sourcedocs/nextjs/pages/ | wc -l

# 2. Check intelligence analysis results
test -f ../workspace/sourcedocs/nextjs/intelligence.jsonl && echo "Intelligence analysis complete"

# 3. Test MCP server health
curl -f http://localhost:8080/health && echo "MCP server healthy"

# 4. Verify search functionality
curl -X POST http://localhost:8080/tools/search \
  -H "Content-Type: application/json" \
  -d '{"query": "getting started", "limit": 1}' | jq '.results[0].title'
```

### Performance Benchmarks

```bash
# Run performance benchmark
poetry run contextor benchmark \
  --budget 1000 \
  --output benchmark-results.json

# View results
cat benchmark-results.json | jq '.performance_metrics'
```

## Troubleshooting

### Common Issues

**"No .mdc files found"**
- Verify source directory contains `.md` or `.mdx` files
- Check file permissions and path accessibility
- Ensure source directory is not empty

**Intelligence analysis fails**
- Install intelligence dependencies: `poetry install --extras intelligence`
- Check if spaCy language model is downloaded
- Verify `.mdc` files are valid JSON

**MCP server connection issues**
- Check server is running: `curl http://localhost:8080/health`
- Verify sourcedocs path is correct
- Check firewall and port availability

### Debug Commands

```bash
# Enable debug logging
export CONTEXTOR_LOG_LEVEL=DEBUG

# Test with minimal example
contextor optimize \
  --src /path/to/single/file \
  --out /tmp/test-output \
  --repo test/repo \
  --ref main

# Validate MCP file format
python -c "import json; print(json.load(open('file.mdc')))"
```

## Next Steps

After completing this tutorial, you should:

1. **Customize Project Configurations**: Create configurations for your specific projects
2. **Set Up Production Deployment**: Deploy MCP server in your production environment
3. **Integrate with AI Workflows**: Connect Contextor to your agent engineering pipelines
4. **Monitor and Optimize**: Set up metrics collection and performance monitoring
5. **Contribute**: Help improve Contextor by reporting issues or contributing features

## Additional Resources

- [CLI Reference Guide](../user-guide/cli-reference.md) - Complete command documentation
- [Architecture Overview](../architecture/architecture.md) - System design and principles
- [MCP Server Guide](../quickstart-mcp-server.md) - Detailed server setup
- [Docker Deployment Guide](../deployment/docker-guide.md) - Container deployment options

## Change log

2025-01-12 — Initial end-to-end workflow tutorial with complete setup and integration examples — (Documentation Team)
