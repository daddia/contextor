# Model Context Protocol (MCP) Integration

Contextor generates standardized `.mcp` files that follow the Model Context Protocol specification. This document explains the MCP file format, structure, and how other tools can consume these files.

## What is MCP?

The Model Context Protocol (MCP) is a standardized format for representing contextual information that AI models and agents can understand and process. MCP files contain both the raw content and structured metadata that enables efficient retrieval, processing, and reasoning.

## MCP File Format (`.mdc`)

Contextor generates `.mdc` files (Model Context Documents) in YAML format with the following structure:

### Basic Structure

```yaml
# MCP Header - Required metadata
mcp_version: "1.0"
generated_by: "contextor"
generated_at: "2025-01-15T10:30:00Z"

# Source Information - Where this content came from
source:
  url: "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts"
  title: "System Prompts"
  site: "anthropic-docs"
  site_name: "Anthropic Documentation"
  fetched_at: "2025-01-15T10:30:00Z"
  content_hash: "sha256:abc123def456..."
  content_length: 4521

# Structured Content - The actual information
content:
  title: "System Prompts"
  summary: "Guide to writing effective system prompts for Claude"
  sections:
    - heading: "What are System Prompts?"
      level: 2
      content: |
        System prompts are instructions that guide the AI's behavior throughout
        the entire conversation. They set the context, tone, and constraints for
        how the AI should respond.
      
    - heading: "Best Practices"
      level: 2
      content: |
        When crafting system prompts, consider these key principles:
      subsections:
        - heading: "Be Specific and Clear"
          level: 3
          content: |
            Specific instructions lead to more consistent and predictable AI behavior.
            Instead of "be helpful," try "provide step-by-step explanations with examples."

# Context Metadata - For discovery and relationships
context:
  topics: ["prompt-engineering", "system-prompts", "AI-guidance", "claude"]
  content_type: "documentation"
  language: "en"
  related_pages: 
    - "anthropic-docs/pages/be-clear-and-direct.mdc"
    - "anthropic-docs/pages/prompt-engineering-overview.mdc"
  last_modified: "2025-01-14T15:20:00Z"
  word_count: 892
  reading_time_minutes: 4
```

## Directory Structure

MCP files are organized in the `{source-slug}/` directory:

```
{source-slug}/
├── manifest.json                    # Global manifest
├── anthropic-docs/
│   ├── manifest.json               # Site manifest
│   ├── index.json                  # Page index
│   └── pages/
│       ├── system-prompts.mdc
│       ├── be-clear-and-direct.mdc
│       └── prompt-engineering-overview.mdc
└── openai-docs/
    ├── manifest.json
    ├── index.json
    └── pages/
        ├── prompt-engineering-guide.mdc
        └── agents-overview.mdc
```

### Manifest Files

#### Global Manifest (`{source-slug}/manifest.json`)

```json
{
  "mcp_version": "1.0",
  "generated_by": "contextor",
  "generated_at": "2025-01-15T10:30:00Z",
  "sites": [
    {
      "slug": "anthropic-docs",
      "name": "Anthropic Documentation",
      "base_url": "https://docs.anthropic.com",
      "pages_count": 23,
      "last_updated": "2025-01-15T10:30:00Z"
    },
    {
      "slug": "openai-docs", 
      "name": "OpenAI Platform Documentation",
      "base_url": "https://platform.openai.com",
      "pages_count": 15,
      "last_updated": "2025-01-15T10:25:00Z"
    }
  ],
  "total_pages": 38,
  "total_sites": 2
}
```

#### Site Manifest (`{source-slug}/{site}/manifest.json`)

```json
{
  "site_slug": "anthropic-docs",
  "site_name": "Anthropic Documentation", 
  "base_url": "https://docs.anthropic.com",
  "mcp_version": "1.0",
  "generated_at": "2025-01-15T10:30:00Z",
  "pages": [
    {
      "slug": "system-prompts",
      "title": "System Prompts",
      "url": "https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/system-prompts",
      "file": "pages/system-prompts.mdc",
      "content_hash": "sha256:abc123...",
      "topics": ["prompt-engineering", "system-prompts"],
      "word_count": 892,
      "last_modified": "2025-01-14T15:20:00Z"
    }
  ],
  "total_pages": 23,
  "topics": ["prompt-engineering", "claude", "AI-guidance", "system-prompts"],
  "last_crawled": "2025-01-15T10:30:00Z"
}
```

## Using MCP Files in Your Project

### Python Integration

```python
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

class MCPReader:
    def __init__(self, context_dir: str = "{source-slug}"):
        self.context_dir = Path(context_dir)
    
    def load_manifest(self) -> Dict[str, Any]:
        """Load the global manifest"""
        manifest_path = self.context_dir / "manifest.json"
        with open(manifest_path) as f:
            return json.load(f)
    
    def load_site_manifest(self, site_slug: str) -> Dict[str, Any]:
        """Load manifest for a specific site"""
        manifest_path = self.context_dir / site_slug / "manifest.json"
        with open(manifest_path) as f:
            return json.load(f)
    
    def load_mcp_file(self, site_slug: str, page_slug: str) -> Dict[str, Any]:
        """Load a specific MCP file"""
        mcp_path = self.context_dir / site_slug / "pages" / f"{page_slug}.mdc"
        with open(mcp_path) as f:
            return yaml.safe_load(f)
    
    def find_pages_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Find all pages containing a specific topic"""
        pages = []
        for site_dir in self.context_dir.iterdir():
            if site_dir.is_dir() and (site_dir / "manifest.json").exists():
                site_manifest = self.load_site_manifest(site_dir.name)
                for page in site_manifest["pages"]:
                    if topic in page.get("topics", []):
                        mcp_data = self.load_mcp_file(site_dir.name, page["slug"])
                        pages.append(mcp_data)
        return pages
    
    def get_all_topics(self) -> List[str]:
        """Get all unique topics across all sites"""
        topics = set()
        manifest = self.load_manifest()
        for site in manifest["sites"]:
            site_manifest = self.load_site_manifest(site["slug"])
            topics.update(site_manifest.get("topics", []))
        return sorted(topics)

# Example usage
reader = MCPReader()
manifest = reader.load_manifest()
print(f"Found {manifest['total_pages']} pages across {manifest['total_sites']} sites")

# Find all prompt engineering content
pe_pages = reader.find_pages_by_topic("prompt-engineering")
for page in pe_pages:
    print(f"- {page['content']['title']} from {page['source']['site_name']}")
```

### Command Line Tools

```bash
# Find pages by topic
contextor search --topic "prompt-engineering" --context-dir {source-slug}

# List all available topics  
contextor topics --context-dir {source-slug}

# Export to different formats
contextor export --format json --output prompt_engineering.json --topic "prompt-engineering"
contextor export --format markdown --output pe_docs.md --site anthropic-docs
```

## Integration Examples

### With Vector Databases

```python
from typing import List
import chromadb

class MCPVectorStore:
    def __init__(self, context_dir: str = "{source-slug}"):
        self.reader = MCPReader(context_dir)
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("mcp_docs")
    
    def index_all_content(self):
        """Index all MCP content in vector database"""
        manifest = self.reader.load_manifest()
        
        for site in manifest["sites"]:
            site_manifest = self.reader.load_site_manifest(site["slug"])
            
            for page in site_manifest["pages"]:
                mcp_data = self.reader.load_mcp_file(site["slug"], page["slug"])
                
                # Extract text content
                content_text = self._extract_text_content(mcp_data)
                
                # Add to vector store
                self.collection.add(
                    documents=[content_text],
                    metadatas=[{
                        "site": site["slug"],
                        "title": mcp_data["content"]["title"],
                        "url": mcp_data["source"]["url"],
                        "topics": mcp_data["context"]["topics"]
                    }],
                    ids=[f"{site['slug']}-{page['slug']}"]
                )
    
    def search_similar(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar content"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
```

### With LangChain

```python
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

class MCPLangChainLoader:
    def __init__(self, context_dir: str = "{source-slug}"):
        self.reader = MCPReader(context_dir)
    
    def load_documents(self, site_slug: str = None, topic: str = None) -> List[Document]:
        """Load MCP files as LangChain Documents"""
        documents = []
        
        if topic:
            pages = self.reader.find_pages_by_topic(topic)
        else:
            # Load all pages from a site or all sites
            manifest = self.reader.load_manifest()
            pages = []
            
            sites_to_process = [site_slug] if site_slug else [s["slug"] for s in manifest["sites"]]
            
            for site in sites_to_process:
                site_manifest = self.reader.load_site_manifest(site)
                for page in site_manifest["pages"]:
                    pages.append(self.reader.load_mcp_file(site, page["slug"]))
        
        for mcp_data in pages:
            content = self._extract_text_content(mcp_data)
            
            doc = Document(
                page_content=content,
                metadata={
                    "source": mcp_data["source"]["url"],
                    "title": mcp_data["content"]["title"],
                    "site": mcp_data["source"]["site"],
                    "topics": mcp_data["context"]["topics"],
                    "content_hash": mcp_data["source"]["content_hash"]
                }
            )
            documents.append(doc)
        
        return documents
```

## Best Practices for MCP Consumers

1. **Check MCP Version**: Always verify the `mcp_version` to ensure compatibility
2. **Use Content Hashes**: Leverage `content_hash` for caching and change detection
3. **Respect Topics**: Use the `topics` metadata for efficient filtering
4. **Handle Missing Files**: Gracefully handle cases where referenced MCP files don't exist
5. **Cache Manifests**: Cache manifest files to avoid repeatedly parsing them
6. **Index Structure**: Use the hierarchical structure (manifest → site → pages) for efficient access

## MCP Schema Validation

Contextor includes schema validation to ensure generated MCP files are well-formed:

```bash
# Validate all MCP files
contextor validate --context-dir {source-slug}

# Validate specific site
contextor validate --context-dir {source-slug} --site anthropic-docs

# Show validation schema
contextor schema --format yaml
```
