# Project Configurations

This directory contains JSON project configurations that align with evolving standard advanced configuration structure. These configurations provide comprehensive metadata and settings for processing documentation from popular open-source projects.

## Configuration Structure

Each project configuration follows this JSON schema:

```json
{
  "settings": {
    "title": "Project Name",
    "private": false,
    "project": "/owner/repository",
    "docsRepoUrl": "https://github.com/owner/repository",
    "folders": ["docs", "api"],
    "excludeFolders": ["archive", "legacy", "i18n/*"],
    "branch": "main",
    "description": "Project description",
    "approved": true,
    "stars": 50000,
    "trustScore": 10,
    "vip": true,
    "excludeFiles": ["CHANGELOG.md", "LICENSE.md"],
    "type": "repo",
    "topics": ["framework", "javascript"],
    "profile": "balanced",
    "transforms": {
      "mdx_components": ["Callout", "Card"],
      "code_block_rules": {
        "preserve_languages": ["jsx", "tsx"],
        "max_lines": 30
      },
      "link_rules": {
        "base_url": "https://example.com",
        "preserve_anchors": true
      }
    }
  },
  "tags": {}
}
```

## Available Configurations

- **`nextjs.json`** - Next.js React framework documentation
- **`react.json`** - React library documentation
- **`tailwindcss.json`** - Tailwind CSS utility framework
- **`vscode.json`** - Visual Studio Code editor documentation
- **`vite.json`** - Vite build tool documentation

## Usage

### CLI Usage

List available project configurations:
```bash
poetry run contextor list-projects
```

Use a project configuration for optimization:
```bash
poetry run contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --project-config nextjs
```

When using `--project-config`, the following parameters are automatically set from the configuration:
- `--repo` (derived from `docsRepoUrl`)
- `--ref` (from `branch`)
- `--topics` (from `topics` array)
- `--profile` (from `profile`)

You can still override these by providing them explicitly:
```bash
poetry run contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --project-config nextjs \
  --ref main \
  --topics "custom,topics"
```

### Automatic Config Detection

Contextor automatically detects standards-based config files in source repositories:

```bash
# Auto-detection enabled by default
poetry run contextor optimize \
  --src /path/to/docs \
  --out /path/to/output

# Disable auto-detection
poetry run contextor optimize \
  --src /path/to/docs \
  --out /path/to/output \
  --no-auto-detect-config
```

### GitHub Actions Integration

The matrix workflow automatically uses project configurations:

```yaml
- name: Run contextor optimize
  run: |
    poetry run contextor optimize \
      --src "../upstream/${{ matrix.source_slug }}/docs" \
      --out "../sourcedocs/${{ matrix.source_slug }}" \
      --project-config "${{ matrix.source_slug }}" \
      --metrics-output "../sourcedocs/${{ matrix.source_slug }}/metrics.json"
```

## Configuration Fields

### Core Settings

- **`title`** - Human-readable project name
- **`project`** - Repository path (e.g., "/vercel/next.js")
- **`docsRepoUrl`** - Full GitHub repository URL
- **`folders`** - Array of documentation folders to include
- **`excludeFolders`** - Array of folder patterns to exclude
- **`branch`** - Default branch to process
- **`description`** - Project description

### Quality Metadata

- **`approved`** - Whether the project is approved for processing
- **`stars`** - GitHub star count (for reference)
- **`trustScore`** - Trust score (1-10)
- **`vip`** - Whether this is a VIP project
- **`type`** - Project type ("repo")

### Processing Settings

- **`excludeFiles`** - Array of file patterns to exclude
- **`topics`** - Array of topic tags for content
- **`profile`** - Optimization profile ("lossless", "balanced", "compact")

### Transform Configuration

- **`transforms.mdx_components`** - MDX components to handle specially
- **`transforms.code_block_rules`** - Code block processing rules
- **`transforms.link_rules`** - Link rewriting rules

## Creating New Configurations

To create a new project configuration:

1. Create a new JSON file: `config/projects/myproject.json`
2. Follow the schema structure above
3. Test with: `poetry run contextor list-projects`
4. Use with: `poetry run contextor optimize --project-config myproject`

## Standards Config Integration

This system is fully aligned with standards and provides:

- **Automatic detection**: Contextor automatically detects and syncs with other standards-based config files (e.g. `context7.json`) in source repositories
- **Standards compliance**: Full compatibility with standards configuration format
- **Live synchronization**: Keeps local configurations updated with upstream changes
- **Metadata preservation**: Maintains trust scores, approval status, and VIP flags
