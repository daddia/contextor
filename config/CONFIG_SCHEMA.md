# Project Configuration Schema

This document describes the complete schema for project configuration files used by contextor.

## File Structure

Project configurations are stored in `config/projects/{project-name}.json` and follow this structure:

```json
{
  "settings": { /* Core project settings */ },
  "tags": { /* Custom tags and metadata */ },
  "metadata": { /* Scan history and tracking (auto-generated) */ }
}
```

## Settings Section

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Human-readable project name | `"Next.js"` |
| `project` | string | Repository path identifier | `"/vercel/next.js"` |
| `docsRepoUrl` | string | Full GitHub repository URL | `"https://github.com/vercel/next.js"` |
| `folders` | array | Documentation folders to process | `["docs", "api"]` |
| `branch` | string | Git branch to use | `"main"` or `"canary"` |

### Optional Fields

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `private` | boolean | Whether repository is private | `false` |
| `excludeFolders` | array | Folders to exclude from processing | `[]` |
| `excludeFiles` | array | Files to exclude from processing | `[]` |
| `description` | string | Project description | `""` |
| `approved` | boolean | Whether project is approved for processing | `true` |
| `stars` | number | GitHub stars count | `0` |
| `trustScore` | number | Trust score (1-10) | `5` |
| `vip` | boolean | Whether project has VIP status | `false` |
| `type` | string | Project type | `"repo"` |
| `topics` | array | Content topics/tags | `[]` |
| `profile` | string | Processing profile | `"balanced"` |

### Transform Configuration

The `transforms` object configures content processing:

```json
{
  "transforms": {
    "mdx_components": [
      "Callout",
      "Card",
      "Tabs",
      "CodeBlock"
    ],
    "code_block_rules": {
      "preserve_languages": ["jsx", "tsx", "javascript", "typescript"],
      "max_lines": 30
    },
    "link_rules": {
      "base_url": "https://example.com",
      "preserve_anchors": true
    }
  }
}
```

## Tags Section

Custom metadata and categorization:

```json
{
  "tags": {
    "priority": "high",
    "category": "framework",
    "maintenance": "active",
    "team": "frontend",
    "custom_field": "custom_value"
  }
}
```

## Metadata Section (Auto-Generated)

**⚠️ This section is automatically managed by contextor and should not be edited manually.**

### Current Scan Status

```json
{
  "metadata": {
    "last_scanned_at": "2025-09-01T12:30:00.000000Z",
    "last_scan_duration": 8.5,
    "last_scan_stats": {
      "files": 150,
      "written": 148,
      "errors": 2,
      "tokens": 125000
    },
    "last_scan_source": {
      "branch": "main",
      "commit": "abc123def456"
    }
  }
}
```

### Scan History

Tracks up to 10 recent scans:

```json
{
  "scan_history": [
    {
      "timestamp": "2025-09-01T12:30:00.000000Z",
      "duration": 8.5,
      "files": 150,
      "tokens": 125000,
      "success": true
    }
  ]
}
```

### Optional Scheduling (Future)

```json
{
  "refresh_schedule": {
    "frequency": "daily",
    "last_check": "2025-09-01T12:30:00.000000Z",
    "next_scheduled": "2025-09-02T12:30:00.000000Z",
    "auto_refresh": true
  }
}
```

## Processing Profiles

| Profile | Description | Use Case |
|---------|-------------|----------|
| `lossless` | No compression, preserve all content | Critical documentation |
| `balanced` | Moderate compression, good quality | Most projects (default) |
| `compact` | Aggressive compression, smaller output | Large corpora |

## Common Configuration Patterns

### Framework Documentation
```json
{
  "settings": {
    "folders": ["docs"],
    "topics": ["framework", "javascript"],
    "profile": "balanced",
    "transforms": {
      "mdx_components": ["Callout", "CodeBlock", "Tabs"],
      "code_block_rules": {
        "preserve_languages": ["jsx", "tsx", "javascript"],
        "max_lines": 30
      }
    }
  }
}
```

### API Reference Documentation
```json
{
  "settings": {
    "folders": ["api", "reference"],
    "topics": ["api", "reference"],
    "profile": "lossless",
    "transforms": {
      "code_block_rules": {
        "preserve_languages": ["json", "yaml", "bash"],
        "max_lines": 50
      }
    }
  }
}
```

### Component Library
```json
{
  "settings": {
    "folders": ["components", "docs"],
    "topics": ["components", "ui", "design-system"],
    "profile": "balanced",
    "transforms": {
      "mdx_components": ["ComponentPreview", "ComponentSource", "Tabs"],
      "code_block_rules": {
        "preserve_languages": ["tsx", "jsx"],
        "max_lines": 40
      }
    }
  }
}
```

## Usage Examples

### Create New Project Config
1. Copy `config/project.example.json` to `config/projects/myproject.json`
2. Update the settings for your project
3. Run: `poetry run contextor fetch --project-config myproject --out ./sourcedocs`

### View Scan History
```bash
# All projects
poetry run contextor scan-history --detailed

# Specific project
poetry run contextor scan-history --project myproject --detailed
```

### Batch Processing
```bash
# Process multiple configured projects
poetry run contextor batch-fetch --projects "nextjs,react,myproject" --out ./sourcedocs
```

## Validation

The configuration is validated when loaded. Common issues:

- **Missing required fields**: `title`, `project`, `docsRepoUrl`, `folders`, `branch`
- **Invalid JSON syntax**: Use a JSON validator
- **Invalid folder paths**: Ensure folders exist in the repository
- **Invalid branch**: Ensure branch exists in the repository

## Best Practices

1. **Use descriptive titles**: Help identify projects quickly
2. **Specify exact folders**: Avoid processing unnecessary content
3. **Configure exclusions**: Skip legacy, archived, or translated content
4. **Set appropriate topics**: Enable better content categorization
5. **Choose right profile**: Balance quality vs. size based on use case
6. **Don't edit metadata**: Let contextor manage scan history automatically

## Integration with CI/CD

The metadata enables intelligent refresh scheduling:

```bash
# Check if refresh needed (pseudo-code)
if last_scanned > 24_hours_ago or token_count_changed > 10%:
    poetry run contextor fetch --project-config $PROJECT --out ./sourcedocs
fi
```

This configuration system provides a complete foundation for automated, scalable documentation processing with intelligent refresh capabilities.
