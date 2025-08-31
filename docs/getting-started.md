---
title: "Getting Started with Contextor"
canonical_id: "DOC-GS-001"
version: "1.0.0"
updated: "2025-01-12"
owner: "Contextor Team"
status: "approved"
tags: ["getting-started", "tutorial", "setup"]
source_url: "https://github.com/daddia/contextor/docs/getting-started.md"
---

# Getting Started with Contextor [ID: DOC-GS-001]

Contextor converts existing documentation directories from repositories into **Model Context Protocol** (`.mdc`) files optimized for LLMs. This guide will help you set up and use Contextor to process documentation directories and generate optimized MCP files for your project.

## Summary

- Install Contextor using Poetry for dependency management
- Process local documentation directories with the `optimize` command
- Generate `.mdc` files with rich metadata and content optimization
- Use project configurations for popular frameworks like Next.js and React
- Deploy MCP server for agent integration (Phase 2)
- Leverage intelligence analysis for content insights

## Installation

### Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- Git

### Install Contextor

```bash
# Clone the repository
git clone https://github.com/daddia/contextor.git
cd contextor

# Install dependencies using Poetry
poetry install

# Optional: Install intelligence analysis features
poetry install --extras intelligence

# Optional: Install serverless deployment features
poetry install --extras aws
```

### Install as a Package

```bash
# Install from PyPI (when available)
pip install contextor

# Or install from source
pip install git+https://github.com/daddia/contextor.git
```

## Quick Start

### 1. Prepare Your Documentation

Contextor works with local documentation directories from repositories. First, clone the documentation you want to process:

```bash
# Example: Clone Next.js documentation
git clone https://github.com/vercel/next.js.git ../vendor/nextjs
cd ../vendor/nextjs
git checkout main  # or specific branch/commit

# Create output directory
mkdir -p ../sourcedocs
```

### 2. Process Documentation

Use the `optimize` command to convert documentation to `.mdc` files:

```bash
# Basic usage
poetry run contextor optimize \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/nextjs \
  --repo vercel/next.js \
  --ref main

# Using project configuration (recommended)
poetry run contextor optimize \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/nextjs \
  --project-config nextjs
```

### 3. Explore the Results

Your `../sourcedocs/nextjs/` directory now contains:

```text
sourcedocs/nextjs/
├── pages/
│   ├── getting-started.mdc      # Optimized MCP files
│   ├── routing.mdc
│   └── api-reference.mdc
├── index.jsonl                  # Document index
└── metrics.json                 # Processing metrics
```

### 4. Use in Your Project

```python
import json
from pathlib import Path

# Load MCP files
sourcedocs_dir = Path("../sourcedocs/nextjs/pages")
for mdc_file in sourcedocs_dir.glob("*.mdc"):
    with open(mdc_file) as f:
        mdc_data = json.load(f)
        print(f"Title: {mdc_data['content']['title']}")
        print(f"Source: {mdc_data['source']['canonical_url']}")
        print(f"Topics: {mdc_data['metadata']['topics']}")
```

## CLI Commands

### Core Commands

#### optimize
Convert a documentation directory to `.mdc` files:

```bash
# Required parameters
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --repo owner/repository \
  --ref branch-or-commit

# With project configuration
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --project-config nextjs

# Additional options
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --repo owner/repository \
  --ref main \
  --topics "framework,javascript" \
  --profile balanced \
  --metrics-output metrics.json
```

#### list-projects
List available project configurations:

```bash
contextor list-projects
```

#### intelligence
Run intelligence analysis on processed `.mdc` files:

```bash
contextor intelligence \
  --source-dir /path/to/mdc/files \
  --features topic-extraction,cross-linking,quality-scoring \
  --metrics-output intelligence-metrics.json
```

### Optimization Profiles

- **`lossless`**: Preserve all content with minimal changes
- **`balanced`**: Optimize for readability while preserving meaning (default)
- **`compact`**: Aggressive optimization for token efficiency

### Project Configurations

Contextor includes built-in configurations for popular projects:

- `nextjs` - Next.js React framework
- `react` - React library
- `tailwindcss` - Tailwind CSS framework
- `vite` - Vite build tool
- `vscode` - Visual Studio Code

## Directory-Based Workflow

### Phase 1: Local Processing

Contextor's Phase 1 focuses on **directory-first ingestion** with no network calls during optimization:

1. **Source Preparation**: Clone the target repository locally
2. **Directory Processing**: Point Contextor at the documentation directory
3. **Content Transformation**: Apply normalization and optimization transforms
4. **MCP Generation**: Output `.mdc` files with rich metadata
5. **Indexing**: Generate searchable index files

### Phase 2: MCP Server (Optional)

Deploy a read-only MCP server to serve your processed content:

```bash
# Start MCP server locally
poetry run contextor-server --transport=stdio

# Or with HTTP transport
poetry run contextor-server --transport=sse --host=0.0.0.0 --port=8080
```

## Project Configuration

### Using Built-in Configurations

```bash
# List available configurations
contextor list-projects

# Use a specific configuration
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --project-config nextjs
```

### Automatic Configuration Detection

Contextor automatically detects standards-based configuration files:

```bash
# Auto-detection enabled by default
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output

# Disable auto-detection
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --no-auto-detect-config
```

### Custom Configuration

Create a custom project configuration in `config/projects/myproject.json`:

```json
{
  "settings": {
    "title": "My Project",
    "project": "/owner/repository",
    "docsRepoUrl": "https://github.com/owner/repository",
    "folders": ["docs", "guides"],
    "excludeFolders": ["archive", "legacy"],
    "branch": "main",
    "description": "Custom project description",
    "topics": ["custom", "documentation"],
    "profile": "balanced"
  }
}
```

## Intelligence Analysis

### Enable Advanced Features

```bash
# Install intelligence dependencies
poetry install --extras intelligence

# Run analysis with all features
contextor intelligence \
  --source-dir /path/to/mdc/files \
  --features topic-extraction,cross-linking,quality-scoring,duplicate-detection
```

### Analysis Features

- **Topic Extraction**: Automatically identify document topics
- **Cross-Linking**: Find relationships between documents
- **Quality Scoring**: Assess content completeness and clarity
- **Duplicate Detection**: Identify similar or duplicate content

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/update-context.yml
name: Update Context
on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday at 6 AM
  workflow_dispatch:

jobs:
  update-context:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Install Contextor
        run: poetry install

      - name: Process Documentation
        run: |
          poetry run contextor optimize \
            --src ../vendor/nextjs/docs \
            --out ../sourcedocs/nextjs \
            --project-config nextjs \
            --metrics-output metrics.json

      - name: Run Intelligence Analysis
        run: |
          poetry run contextor intelligence \
            --source-dir ../sourcedocs/nextjs \
            --features topic-extraction,cross-linking,quality-scoring

      - name: Commit Changes
        run: |
          git config --local user.name "GitHub Actions"
          git config --local user.email "action@github.com"
          git add ../sourcedocs/
          git commit -m "Update context: $(date -I)" || exit 0
          git push
```

### Python Integration

```python
# your_project/context_manager.py
import subprocess
from pathlib import Path
import json

class ContextManager:
    def __init__(self, sourcedocs_dir="../sourcedocs", project_config="nextjs"):
        self.sourcedocs_dir = Path(sourcedocs_dir)
        self.project_config = project_config

    def update_documentation(self, src_dir: str, output_dir: str):
        """Process documentation using contextor"""
        subprocess.run([
            "poetry", "run", "contextor", "optimize",
            "--src", src_dir,
            "--out", output_dir,
            "--project-config", self.project_config
        ], check=True)

    def load_documents_by_topic(self, topic: str, source_slug: str):
        """Load all documents containing a specific topic"""
        documents = []
        pages_dir = self.sourcedocs_dir / source_slug / "pages"

        if pages_dir.exists():
            for mdc_file in pages_dir.glob("*.mdc"):
                with open(mdc_file) as f:
                    mdc_data = json.load(f)
                    if topic in mdc_data.get("metadata", {}).get("topics", []):
                        documents.append(mdc_data)

        return documents

    def get_intelligence_results(self, source_slug: str):
        """Get intelligence analysis results"""
        intelligence_file = self.sourcedocs_dir / source_slug / "intelligence.jsonl"

        results = []
        if intelligence_file.exists():
            with open(intelligence_file) as f:
                for line in f:
                    results.append(json.loads(line))

        return results

# Usage example
context_manager = ContextManager()

# Update documentation
context_manager.update_documentation(
    "../vendor/nextjs/docs",
    "../sourcedocs/nextjs"
)

# Use the processed content
react_docs = context_manager.load_documents_by_topic("hooks", "react")
for doc in react_docs:
    print(f"Processing: {doc['content']['title']}")
    # Your processing logic here
```

## Troubleshooting

### Common Issues

#### Missing Required Parameters
```bash
# Error: Missing required parameters
# Solution: Provide all required parameters or use project config
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --repo owner/repository \
  --ref main
```

#### Project Configuration Not Found
```bash
# Check available configurations
contextor list-projects

# Use exact configuration name
contextor optimize --project-config nextjs  # not "Next.js"
```

#### No Files Processed
```bash
# Check source directory structure
ls -la /path/to/docs/

# Ensure directory contains .md or .mdx files
find /path/to/docs -name "*.md" -o -name "*.mdx" | head -10
```

#### Intelligence Analysis Errors
```bash
# Install intelligence dependencies
poetry install --extras intelligence

# Run with specific features only
contextor intelligence \
  --source-dir /path/to/mdc/files \
  --features topic-extraction
```

### Debug Mode

```bash
# Enable verbose logging
export CONTEXTOR_LOG_LEVEL=DEBUG
contextor optimize --src /path/to/docs --out /path/to/output --repo owner/repo --ref main

# Save processing metrics
contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --repo owner/repo \
  --ref main \
  --metrics-output debug-metrics.json
```

### Getting Help

```bash
# Show help for any command
contextor --help
contextor optimize --help
contextor intelligence --help

# List available project configurations
contextor list-projects
```

## Next Steps

1. **Explore Project Configurations**: Use built-in configurations for popular frameworks
2. **Set Up Intelligence Analysis**: Enable advanced content analysis features
3. **Deploy MCP Server**: Set up the MCP server for agent integration
4. **Automate Processing**: Create CI/CD pipelines for regular updates
5. **Customize Transforms**: Configure content transformation rules for your needs

## Change log

2025-01-12 — Updated to reflect current directory-based workflow, removed outdated web scraping examples, added project configuration guidance — (Documentation Team)
