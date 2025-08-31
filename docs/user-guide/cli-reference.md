---
title: "CLI Command Reference"
canonical_id: "DOC-CLI-001"
version: "1.0.0"
updated: "2025-01-12"
owner: "Contextor Team"
status: "approved"
tags: ["cli", "reference", "commands"]
source_url: "https://github.com/daddia/contextor/docs/user-guide/cli-reference.md"
---

# CLI Command Reference [ID: DOC-CLI-001]

Complete reference for all Contextor CLI commands and options.

## Summary

- `optimize` command processes documentation directories into `.mdc` files
- `intelligence` command runs advanced content analysis
- `list-projects` command shows available project configurations
- Global options control logging, output format, and behavior
- Project configurations simplify complex command invocations
- All commands support `--help` for detailed usage information

## Global Options

Available for all commands:

```bash
--help          Show help message and exit
--version       Show version information
--verbose       Enable verbose logging output
--quiet         Suppress non-error output
--log-level     Set logging level (DEBUG, INFO, WARNING, ERROR)
```

## Commands

### optimize

Convert a documentation directory to `.mdc` files with rich metadata and content optimization.

#### Syntax

```bash
contextor optimize [OPTIONS]
```

#### Required Options

```bash
--src PATH              Source directory containing Markdown/MDX files
--out PATH              Output directory for .mdc files
--repo STRING           Repository identifier (e.g., 'vercel/next.js')
--ref STRING            Git reference (branch or commit SHA)
```

#### Optional Options

```bash
--topics STRING         Comma-separated list of topics to tag content
--profile STRING        Optimization profile: lossless, balanced, or compact
                       (default: balanced)
--project-config STRING Project configuration name (e.g., 'nextjs', 'react')
--auto-detect-config    Automatically detect standards-based config files
                       (default: enabled)
--metrics-output PATH   Output path for processing metrics JSON
```

#### Examples

**Basic Usage:**
```bash
contextor optimize \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/nextjs \
  --repo vercel/next.js \
  --ref main
```

**With Project Configuration:**
```bash
contextor optimize \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/nextjs \
  --project-config nextjs
```

**Custom Topics and Profile:**
```bash
contextor optimize \
  --src ../vendor/react/docs \
  --out ../sourcedocs/react \
  --repo facebook/react \
  --ref main \
  --topics "framework,javascript,ui" \
  --profile compact
```

**With Metrics Output:**
```bash
contextor optimize \
  --src ../vendor/tailwind/docs \
  --out ../sourcedocs/tailwind \
  --project-config tailwindcss \
  --metrics-output processing-metrics.json
```

#### Optimization Profiles

**lossless**
- Preserves all content with minimal changes
- No content compression or elision
- Maximum fidelity to original documentation

**balanced** (default)
- Optimizes for readability while preserving meaning
- Moderate content normalization
- Good balance between token efficiency and completeness

**compact**
- Aggressive optimization for token efficiency
- Content compression and safe elision
- Ideal for large documentation sets

#### Project Configuration Integration

When using `--project-config`, the following parameters are automatically set:
- `--repo` (derived from configuration)
- `--ref` (from branch setting)
- `--topics` (from topics array)
- `--profile` (from profile setting)

You can override these by providing them explicitly.

### intelligence

Run advanced content analysis on processed `.mdc` files to extract insights and relationships.

#### Syntax

```bash
contextor intelligence [OPTIONS]
```

#### Required Options

```bash
--source-dir PATH       Directory containing .mdc files to analyze
```

#### Optional Options

```bash
--features STRING       Comma-separated list of features to enable
                       (default: topic-extraction,cross-linking,quality-scoring,duplicate-detection)
--config PATH          Path to intelligence configuration YAML file
--incremental          Run incremental analysis (skip unchanged files)
                       (default: enabled)
--full                 Run full analysis on all files
--metrics-output PATH  Output path for analysis metrics JSON
```

#### Available Features

**topic-extraction**
- Automatically identify document topics using NLP
- Extract semantic themes from content
- Generate topic hierarchies

**cross-linking**
- Find relationships between documents
- Suggest internal links based on content similarity
- Build document dependency graphs

**quality-scoring**
- Assess content completeness and clarity
- Rate freshness and accuracy
- Provide improvement recommendations

**duplicate-detection**
- Identify similar or duplicate content
- Find content overlap between documents
- Suggest consolidation opportunities

#### Examples

**Basic Intelligence Analysis:**
```bash
contextor intelligence \
  --source-dir ../sourcedocs/nextjs
```

**Specific Features Only:**
```bash
contextor intelligence \
  --source-dir ../sourcedocs/react \
  --features topic-extraction,quality-scoring
```

**Full Analysis with Metrics:**
```bash
contextor intelligence \
  --source-dir ../sourcedocs/tailwind \
  --features topic-extraction,cross-linking,quality-scoring,duplicate-detection \
  --full \
  --metrics-output intelligence-metrics.json
```

**With Custom Configuration:**
```bash
contextor intelligence \
  --source-dir ../sourcedocs/vscode \
  --config config/intelligence.yaml \
  --metrics-output analysis-results.json
```

#### Intelligence Configuration

Create `config/intelligence.yaml` for custom analysis settings:

```yaml
topic_extraction:
  min_topic_frequency: 3
  max_topics_per_document: 10
  language_model: "en_core_web_sm"

cross_linking:
  max_related_documents: 5
  topic_overlap_threshold: 0.3
  relevance_threshold: 0.4

quality_scoring:
  completeness_weight: 0.4
  freshness_weight: 0.3
  clarity_weight: 0.3

duplicate_detection:
  similarity_threshold: 0.8
  content_overlap_threshold: 0.7
```

### list-projects

List available project configurations with details.

#### Syntax

```bash
contextor list-projects
```

#### Output

```bash
Available project configurations:
  nextjs: Next.js React framework (vercel/next.js)
  react: React library (facebook/react)
  tailwindcss: Tailwind CSS framework (tailwindlabs/tailwindcss)
  vite: Vite build tool (vitejs/vite)
  vscode: Visual Studio Code (microsoft/vscode)
```

## Common Workflows

### Processing Multiple Projects

```bash
# Process multiple documentation sources
for project in nextjs react tailwindcss; do
  contextor optimize \
    --src "../vendor/$project/docs" \
    --out "../sourcedocs/$project" \
    --project-config "$project"
done
```

### Incremental Updates

```bash
# Process only changed files
contextor optimize \
  --src ../vendor/nextjs/docs \
  --out ../sourcedocs/nextjs \
  --project-config nextjs

# Run incremental intelligence analysis
contextor intelligence \
  --source-dir ../sourcedocs/nextjs \
  --incremental
```

### Makefile Integration

```makefile
# Add to your Makefile
optimize:
	@if [ -z "$(src)" ] || [ -z "$(out)" ] || [ -z "$(repo)" ] || [ -z "$(ref)" ]; then \
		echo "Usage: make optimize src=<docs_dir> out=<output_dir> repo=<owner/name> ref=<branch>"; \
		exit 1; \
	fi
	poetry run contextor optimize --src=$(src) --out=$(out) --repo=$(repo) --ref=$(ref)

# Usage
make optimize src=../vendor/nextjs/docs out=../sourcedocs/nextjs repo=vercel/next.js ref=main
```

## Error Handling

### Common Exit Codes

- `0`: Success
- `1`: General error or user abort
- `2`: Invalid arguments or configuration
- `3`: Source directory not found
- `4`: Processing errors occurred

### Error Messages

**"Source directory does not exist"**
```bash
# Check the path
ls -la /path/to/docs

# Ensure you're in the correct working directory
pwd
```

**"Git reference is required"**
```bash
# Provide --ref parameter
contextor optimize --src docs --out output --repo owner/repo --ref main

# Or use project configuration
contextor optimize --src docs --out output --project-config nextjs
```

**"No .mdc files found"**
```bash
# Check if optimization completed successfully
ls -la /path/to/output/pages/

# Verify source directory contains markdown files
find /path/to/docs -name "*.md" -o -name "*.mdx"
```

## Advanced Usage

### Custom Transform Rules

Configure content transformation in project configuration:

```json
{
  "settings": {
    "transforms": {
      "mdx_components": ["Callout", "Card", "CodeBlock"],
      "code_block_rules": {
        "preserve_languages": ["jsx", "tsx", "typescript"],
        "max_lines": 50,
        "include_filename": true
      },
      "link_rules": {
        "base_url": "https://example.com",
        "preserve_anchors": true,
        "convert_relative": true
      }
    }
  }
}
```

### Performance Optimization

```bash
# Optimize for speed
contextor optimize \
  --src large-docs-directory \
  --out output \
  --project-config myproject \
  --profile compact

# Process with metrics for performance analysis
contextor optimize \
  --src docs \
  --out output \
  --repo owner/repo \
  --ref main \
  --metrics-output performance.json
```

### Batch Processing

```bash
#!/bin/bash
# batch-process.sh

projects=("nextjs" "react" "tailwindcss" "vite")

for project in "${projects[@]}"; do
  echo "Processing $project..."

  contextor optimize \
    --src "../vendor/$project/docs" \
    --out "../sourcedocs/$project" \
    --project-config "$project" \
    --metrics-output "../sourcedocs/$project/metrics.json"

  if [ $? -eq 0 ]; then
    echo "✓ $project processed successfully"
  else
    echo "✗ $project processing failed"
  fi
done
```

## Change log

2025-01-12 — Initial CLI reference documentation with complete command coverage — (Documentation Team)
