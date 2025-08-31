# Getting Started with Contextor

This guide will help you set up and use Contextor to fetch web content and generate MCP files for your project.

## Installation

### Prerequisites

- Python 3.11 or higher
- Git

### Install Contextor

```bash
# Clone the repository
git clone https://github.com/<your-org>/contextor.git
cd contextor

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install Playwright for dynamic content
python -m playwright install
```

### Install as a Package

```bash
# Install from PyPI (when available)
pip install contextor

# Or install from source
pip install git+https://github.com/<your-org>/contextor.git
```

## Quick Start

### 1. Create Configuration

Create a `config/targets.yaml` file to specify what content to fetch:

```yaml
# config/targets.yaml
version: "1.0"
output_dir: "{source-slug}"

sites:
  - slug: anthropic-docs
    name: "Anthropic Documentation"
    base_url: https://docs.anthropic.com
    robots_txt: true
    rate_limit:
      requests_per_second: 2
      concurrent: 3
    extractor: requests
    selector: "main article"
    pages:
      - path: /en/docs/build-with-claude/prompt-engineering/system-prompts
      - path: /en/docs/build-with-claude/prompt-engineering/be-clear-and-direct
      - path: /en/docs/build-with-claude/prompt-engineering/overview
```

### 2. Run Contextor

```bash
# Fetch content and generate MCP files
contextor fetch --config config/targets.yaml

# Check the output
ls -la {source-slug}/
ls -la {source-slug}/anthropic-docs/pages/
```

### 3. Explore the Results

Your `{source-slug}/` directory now contains:

```
{source-slug}/
├── manifest.json                    # Global manifest
└── anthropic-docs/
    ├── manifest.json               # Site-specific manifest
    ├── index.json                  # Page index
    └── pages/
        ├── system-prompts.mdc      # MCP files
        ├── be-clear-and-direct.mdc
        └── overview.mdc
```

### 4. Use in Your Project

```python
import yaml
from pathlib import Path

# Load all MCP files
context_dir = Path("{source-slug}")
for mcp_file in context_dir.rglob("*.mdc"):
    with open(mcp_file) as f:
        mcp_data = yaml.safe_load(f)
        print(f"Title: {mcp_data['content']['title']}")
        print(f"URL: {mcp_data['source']['url']}")
        print(f"Topics: {mcp_data['context']['topics']}")
```

## Configuration Reference

### Basic Site Configuration

```yaml
sites:
  - slug: my-site                    # Unique identifier
    name: "My Documentation Site"    # Human-readable name
    base_url: https://example.com    # Base URL for the site
    robots_txt: true                 # Respect robots.txt (recommended)
    
    # Rate limiting (be polite!)
    rate_limit:
      requests_per_second: 2         # Max requests per second
      concurrent: 3                  # Max concurrent requests
    
    # Content extraction
    extractor: requests              # Use 'playwright' for JS-heavy sites
    selector: "main, article"        # CSS selector for main content
    title_selector: "h1"             # CSS selector for page title
    
    # Pages to fetch (choose one approach)
    pages:
      - path: /docs/page1
      - path: /docs/page2
        title_selector: ".custom-title"  # Override for specific page
    
    # OR: Use sitemap discovery
    sitemap: true
    filters:
      include_patterns:
        - "*/docs/*"
        - "*/guide/*"
      exclude_patterns:
        - "*/api/*"
        - "*/changelog/*"
```

### Advanced Configuration

```yaml
sites:
  - slug: complex-site
    name: "Complex Site Example"
    base_url: https://complex-site.com
    
    # Use Playwright for JavaScript-heavy sites
    extractor: playwright
    playwright_options:
      headless: true
      timeout: 30000
      wait_for: "networkidle"
    
    # Content cleaning
    selector: ".docs-content"
    remove_selectors:
      - ".navigation"
      - ".sidebar"
      - ".advertisement"
      - "[class*='cookie']"
    
    # Custom headers
    headers:
      User-Agent: "Contextor/1.0 (+https://github.com/your-org/contextor)"
      Accept: "text/html,application/xhtml+xml"
    
    # Transform rules
    transforms:
      - type: "remove_empty_headings"
      - type: "normalize_whitespace"
      - type: "fix_relative_links"
        base_url: "https://complex-site.com"
```

## CLI Commands

### Fetch Content

```bash
# Basic fetch
contextor fetch --config config/targets.yaml

# Fetch specific sites only
contextor fetch --sites anthropic-docs,openai-docs

# Dry run (show what would be fetched)
contextor fetch --dry-run --config config/targets.yaml

# Verbose output
contextor fetch --verbose --config config/targets.yaml
```

### Validate and Inspect

```bash
# Validate generated MCP files
contextor validate --context-dir {source-slug}

# Show site information
contextor info --site anthropic-docs

# List all topics
contextor topics --context-dir {source-slug}

# Search for content
contextor search --topic "prompt-engineering" --context-dir {source-slug}
```

### Export and Convert

```bash
# Export to different formats
contextor export --format json --output docs.json
contextor export --format markdown --output docs.md --site anthropic-docs

# Generate fresh manifests
contextor manifest --context-dir {source-slug}
```

## Common Patterns

### Multiple Sites

```yaml
sites:
  - slug: anthropic-docs
    name: "Anthropic Documentation"
    base_url: https://docs.anthropic.com
    # ... configuration
    
  - slug: openai-docs
    name: "OpenAI Documentation"
    base_url: https://platform.openai.com
    # ... configuration
    
  - slug: mcp-spec
    name: "MCP Specification"
    base_url: https://spec.modelcontextprotocol.io
    # ... configuration
```

### Site-Specific Extractors

```yaml
# config/extractors.yaml
extractors:
  default:
    content_selector: "main, article, .content"
    title_selector: "h1, title"
    remove_selectors:
      - ".navigation"
      - ".sidebar"
      - ".footer"
    
  anthropic-docs:
    content_selector: "main article"
    title_selector: "h1.page-title"
    remove_selectors:
      - ".docs-nav"
      - ".page-footer"
      - ".edit-page"
```

### Sitemap Discovery

```yaml
sites:
  - slug: auto-discovery
    name: "Auto Discovery Example"
    base_url: https://example.com
    sitemap: true                    # Use sitemap.xml for page discovery
    filters:
      include_patterns:
        - "*/docs/*"                 # Only fetch documentation pages
        - "*/guides/*"
      exclude_patterns:
        - "*/api/*"                  # Skip API reference
        - "*/blog/*"                 # Skip blog posts
      max_pages: 100                 # Limit total pages
```

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
      
      - name: Install Contextor
        run: pip install contextor
      
      - name: Fetch Content
        run: contextor fetch --config config/targets.yaml
      
      - name: Validate MCP Files
        run: contextor validate --context-dir {source-slug}
      
      - name: Commit Changes
        run: |
          git config --local user.name "GitHub Actions"
          git config --local user.email "action@github.com"
          git add {source-slug}/
          git commit -m "Update context: $(date -I)" || exit 0
          git push
```

### Python Integration

```python
# your_project/context_manager.py
import subprocess
from pathlib import Path
import yaml

class ContextManager:
    def __init__(self, context_dir="{source-slug}", config_file="config/targets.yaml"):
        self.context_dir = Path(context_dir)
        self.config_file = config_file
    
    def update{source-slug}(self):
        """Fetch latest content using contextor"""
        subprocess.run([
            "contextor", "fetch", 
            "--config", self.config_file
        ], check=True)
    
    def load_pages_by_topic(self, topic: str):
        """Load all pages containing a specific topic"""
        pages = []
        for mcp_file in self.context_dir.rglob("*.mdc"):
            with open(mcp_file) as f:
                mcp_data = yaml.safe_load(f)
                if topic in mcp_data.get("context", {}).get("topics", []):
                    pages.append(mcp_data)
        return pages
    
    def get_latest_content(self, site_slug: str):
        """Get all content from a specific site"""
        site_dir = self.context_dir / site_slug / "pages"
        content = []
        
        if site_dir.exists():
            for mcp_file in site_dir.glob("*.mdc"):
                with open(mcp_file) as f:
                    content.append(yaml.safe_load(f))
        
        return content

# Usage in your application
context_manager = ContextManager()

# Update content (run weekly/daily)
context_manager.update{source-slug}()

# Use the content
prompt_engineering_docs = context_manager.load_pages_by_topic("prompt-engineering")
for doc in prompt_engineering_docs:
    print(f"Processing: {doc['content']['title']}")
    # Your processing logic here
```

## Troubleshooting

### Common Issues

#### Rate Limiting
```bash
# Reduce concurrent requests
# In config/targets.yaml:
rate_limit:
  requests_per_second: 1
  concurrent: 1
```

#### JavaScript-Heavy Sites
```yaml
# Switch to Playwright extractor
extractor: playwright
playwright_options:
  headless: true
  timeout: 30000
  wait_for: "networkidle"
```

#### Content Not Extracted Properly
```bash
# Test selectors interactively
contextor test-selector --url "https://example.com/page" --selector "main article"
```

#### Permission Errors
```bash
# Check robots.txt
contextor check-robots --url "https://example.com"

# Ensure proper user agent
# In config/targets.yaml:
headers:
  User-Agent: "YourBot/1.0 (+https://yoursite.com/bot-info)"
```

### Debug Mode

```bash
# Enable verbose logging
export CONTEXTOR_LOG_LEVEL=DEBUG
contextor fetch --config config/targets.yaml

# Save raw HTML for inspection
contextor fetch --save-raw --config config/targets.yaml
```

### Getting Help

```bash
# Show help for any command
contextor --help
contextor fetch --help

# Show configuration schema
contextor schema --format yaml
```

## Next Steps

1. **Customize Extractors**: Create site-specific extraction rules in `config/extractors.yaml`
2. **Automate Updates**: Set up CI/CD to regularly update your `{source-slug}/` directory
3. **Integrate with Your Application**: Use the MCP files in your prompt engineering or AI workflows
4. **Monitor Content Changes**: Set up alerts for significant content changes
5. **Contribute**: Help improve Contextor by reporting issues or contributing new features
