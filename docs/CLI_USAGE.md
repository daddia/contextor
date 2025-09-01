# Contextor CLI Usage Guide

## Overview

Contextor provides multiple CLI commands for processing documentation repositories into optimized `.mdc` files with comprehensive token analysis.

## Commands

### 🚀 `fetch` - Automated Repository Processing

**Recommended approach** - Automatically clones and processes a configured project:

```bash
poetry run contextor fetch --project-config nextjs --out ./sourcedocs
```

**Features:**
- ✅ Automatic repository cloning from project configuration
- ✅ Uses project-specific settings (folders, exclusions, topics, etc.)
- ✅ Integrated token analysis and metadata generation
- ✅ Automatic workspace cleanup
- ✅ Comprehensive metrics output

**Options:**
- `--project-config`: Project name from `config/projects/` (required)
- `--out`: Output directory (will create project subdirectory)
- `--workspace`: Temporary workspace for cloning (default: `/tmp/contextor-workspace`)
- `--keep-workspace`: Keep cloned repositories after processing
- `--metrics-output`: Save detailed metrics to JSON file

### 📦 `batch-fetch` - Multi-Project Processing

Process multiple projects in one command:

```bash
poetry run contextor batch-fetch --projects "nextjs,tailwindcss,react" --out ./sourcedocs
```

**Features:**
- ✅ Sequential processing of multiple projects
- ✅ Comprehensive batch metrics and reporting
- ✅ Individual project success/failure tracking
- ✅ Combined token analysis across all projects

### 📋 `list-projects` - Available Configurations

List all available project configurations:

```bash
poetry run contextor list-projects
```

**Output:**
```
Available project configurations:
  nextjs: Next.js (https://github.com/vercel/next.js)
  react: React (https://github.com/facebook/react)
  tailwindcss: Tailwind CSS (https://github.com/tailwindlabs/tailwindcss.com)
  vite: Vite (https://github.com/vitejs/vite)
  vscode: VS Code (https://github.com/microsoft/vscode)
```

### 🔧 `optimize` - Manual Processing

For custom repositories or manual workflows:

```bash
poetry run contextor optimize \
  --src /path/to/docs \
  --out ./sourcedocs/project \
  --repo owner/repository \
  --ref main \
  --topics "topic1,topic2"
```

### 📊 `tokens` - Token Analysis

Analyze token counts for existing `.mdc` files:

```bash
poetry run contextor tokens --source-dir ./sourcedocs/nextjs --detailed
```

## Project Configuration Structure

Projects are configured in `config/projects/*.json`:

```json
{
  "settings": {
    "title": "Project Name",
    "project": "/owner/repository",
    "docsRepoUrl": "https://github.com/owner/repository",
    "folders": ["docs", "api"],
    "excludeFolders": ["archive", "legacy"],
    "branch": "main",
    "topics": ["framework", "javascript"],
    "profile": "balanced",
    "transforms": {
      "mdx_components": ["Callout", "Card"],
      "code_block_rules": {
        "preserve_languages": ["jsx", "tsx"],
        "max_lines": 30
      }
    }
  }
}
```

## Output Structure

Each processed project creates:

```
sourcedocs/
└── project-name/
    ├── .metadata/
    │   ├── stats.json           # Token analysis summary
    │   └── run-metrics.json     # Processing metrics
    ├── index.jsonl              # File manifest with per-file stats
    └── *.mdc                    # Processed documentation files
```

## Examples

### Single Project with Custom Output
```bash
poetry run contextor fetch \
  --project-config tailwindcss \
  --out ./my-docs \
  --metrics-output ./metrics.json
```

### Batch Processing for Knowledge Base
```bash
poetry run contextor batch-fetch \
  --projects "nextjs,react,tailwindcss,vite" \
  --out ./knowledge-base \
  --metrics-output ./batch-metrics.json
```

### Token Analysis
```bash
# Quick summary
poetry run contextor tokens --source-dir ./sourcedocs/nextjs

# Detailed analysis with JSON export
poetry run contextor tokens \
  --source-dir ./sourcedocs/nextjs \
  --detailed \
  --output ./token-analysis.json
```

## Migration from Manual Workflow

**Old workflow (manual):**
```bash
# Manual cloning and processing
git clone https://github.com/vercel/next.js.git /tmp/nextjs
poetry run contextor optimize \
  --src /tmp/nextjs/docs \
  --out ./sourcedocs/nextjs \
  --repo vercel/next.js \
  --ref canary \
  --topics "framework,nextjs,react"
```

**New workflow (automated):**
```bash
# Single command with project config
poetry run contextor fetch --project-config nextjs --out ./sourcedocs
```

## Performance

**Benchmark results:**
- **Next.js**: 368 files, 287K tokens in ~7 seconds
- **Tailwind CSS**: 249 files, 228K tokens in ~4 seconds
- **Combined**: 617 files, 515K tokens in ~11 seconds

The automated workflow eliminates manual repository management while providing comprehensive token analysis and metadata generation.
