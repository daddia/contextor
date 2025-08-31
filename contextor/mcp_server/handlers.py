"""
Request handlers for Contextor MCP Server tools
"""

import asyncio
import hashlib
import json
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


class ContextorHandlers:
    """
    Handles MCP tool invocations for Contextor
    """
    
    def __init__(self, base_path: Path):
        """
        Initialize handlers with base storage path
        
        Args:
            base_path: Base directory for storage
        """
        self.base_path = base_path
        self.raw_dir = base_path / "_raw"
        self.context_dir = base_path / "{source-slug}"
        
        # Ensure directories exist
        self.raw_dir.mkdir(exist_ok=True)
        self.context_dir.mkdir(exist_ok=True)
        
        logger.info(f"Handlers initialized with base path: {base_path}")
    
    async def fetch_page(
        self,
        url: str,
        selectors: Optional[Dict] = None,
        cache: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch a web page and convert to markdown
        
        Args:
            url: URL to fetch
            selectors: Optional CSS selectors for extraction
            cache: Whether to use cached content
        
        Returns:
            Dictionary with fetch results
        """
        logger.info(f"Fetching page: {url}")
        
        # Extract site and page slugs
        site_slug = self._extract_site_slug(url)
        page_slug = self._extract_page_slug(url)
        
        # Check cache if enabled
        if cache:
            cached = await self._check_cache(site_slug, page_slug)
            if cached:
                logger.info(f"Using cached content for {url}")
                return {
                    "status": "cached",
                    "site": site_slug,
                    "page": page_slug,
                    "raw_path": str(cached["raw_path"]),
                    "mcp_path": str(cached["mcp_path"]),
                    "cached_at": cached["cached_at"]
                }
        
        # Import scraper modules (these would need to be implemented)
        from ..core.scraper import fetch_url
        from ..core.markdown_converter import html_to_markdown
        from ..core.mcp_optimizer import optimize_for{source-slug}
        
        try:
            # Fetch HTML content
            html_content = await fetch_url(url)
            
            # Convert to markdown
            markdown = html_to_markdown(html_content, selectors)
            
            # Store raw markdown
            date_dir = datetime.now().strftime("%Y-%m-%d")
            raw_path = self.raw_dir / site_slug / date_dir / f"{page_slug}.md"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(markdown)
            
            # Update latest symlink
            latest_link = self.raw_dir / site_slug / "latest"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(date_dir)
            
            # Store metadata
            metadata = {
                "url": url,
                "fetched_at": datetime.now().isoformat(),
                "content_hash": hashlib.sha256(markdown.encode()).hexdigest(),
                "word_count": len(markdown.split()),
                "char_count": len(markdown),
                "selectors": selectors
            }
            
            metadata_path = raw_path.parent / "metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2))
            
            # Generate optimized MCP
            mcp_content = optimize_for{source-slug}(markdown, url)
            mcp_path = self.context_dir / site_slug / "pages" / f"{page_slug}.mdc"
            mcp_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(mcp_path, 'w') as f:
                yaml.dump(mcp_content, f, default_flow_style=False)
            
            # Update site index
            await self._update_site_index(site_slug, page_slug, metadata)
            
            logger.info(f"Successfully fetched and stored: {url}")
            
            return {
                "status": "success",
                "site": site_slug,
                "page": page_slug,
                "raw_path": str(raw_path.relative_to(self.base_path)),
                "mcp_path": str(mcp_path.relative_to(self.base_path)),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "url": url
            }
    
    async def search{source-slug}(
        self,
        query: str,
        site_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search through existing context files
        
        Args:
            query: Search query
            site_filter: Optional site to filter by
            limit: Maximum results
        
        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        
        results = []
        search_dir = self.context_dir / site_filter if site_filter else self.context_dir
        
        if not search_dir.exists():
            return []
        
        # Search through MCP files
        for mcp_file in search_dir.rglob("*.mdc"):
            try:
                with open(mcp_file) as f:
                    content = yaml.safe_load(f)
                
                # Convert content to searchable text
                text = self._extract_searchable_text(content)
                
                # Simple relevance scoring
                if query.lower() in text.lower():
                    score = text.lower().count(query.lower())
                    
                    # Extract preview
                    preview = self._extract_preview(text, query)
                    
                    results.append({
                        "file": str(mcp_file.relative_to(self.context_dir)),
                        "site": mcp_file.parts[-3] if len(mcp_file.parts) > 2 else "unknown",
                        "page": mcp_file.stem,
                        "score": score,
                        "preview": preview,
                        "url": content.get("source", {}).get("url", "")
                    })
            
            except Exception as e:
                logger.warning(f"Error searching {mcp_file}: {e}")
                continue
        
        # Sort by relevance and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:limit]
    
    async def get_mcp_file(self, site: str, page: str) -> Dict[str, Any]:
        """
        Retrieve a specific MCP file
        
        Args:
            site: Site slug
            page: Page slug
        
        Returns:
            MCP file content
        """
        mcp_path = self.context_dir / site / "pages" / f"{page}.mdc"
        
        if not mcp_path.exists():
            return {
                "status": "not_found",
                "error": f"MCP file not found: {site}/{page}"
            }
        
        try:
            with open(mcp_path) as f:
                content = yaml.safe_load(f)
            
            return {
                "status": "success",
                "site": site,
                "page": page,
                "content": content,
                "path": str(mcp_path.relative_to(self.base_path))
            }
        
        except Exception as e:
            logger.error(f"Error reading MCP file: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_raw_markdown(
        self,
        site: str,
        page: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve raw markdown content
        
        Args:
            site: Site slug
            page: Page slug
            date: Optional date for versioned content
        
        Returns:
            Raw markdown content
        """
        if date:
            raw_path = self.raw_dir / site / date / f"{page}.md"
        else:
            # Use latest
            raw_path = self.raw_dir / site / "latest" / f"{page}.md"
        
        if not raw_path.exists():
            return {
                "status": "not_found",
                "error": f"Raw markdown not found: {site}/{page}"
            }
        
        try:
            content = raw_path.read_text()
            
            # Get metadata if available
            metadata_path = raw_path.parent / "metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
            
            return {
                "status": "success",
                "site": site,
                "page": page,
                "content": content,
                "metadata": metadata,
                "path": str(raw_path.relative_to(self.base_path))
            }
        
        except Exception as e:
            logger.error(f"Error reading raw markdown: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def list_sites(
        self,
        include_pages: bool = False,
        include_stats: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List available sites and optionally their pages
        
        Args:
            include_pages: Whether to include page listings
            include_stats: Whether to include statistics
        
        Returns:
            List of sites with optional details
        """
        sites = []
        
        for site_dir in self.context_dir.iterdir():
            if not site_dir.is_dir():
                continue
            
            site_info = {
                "slug": site_dir.name,
                "path": str(site_dir.relative_to(self.base_path))
            }
            
            if include_pages or include_stats:
                pages_dir = site_dir / "pages"
                if pages_dir.exists():
                    pages = list(pages_dir.glob("*.mdc"))
                    
                    if include_pages:
                        site_info["pages"] = [p.stem for p in pages]
                    
                    if include_stats:
                        site_info["page_count"] = len(pages)
                        
                        # Get last modified time
                        if pages:
                            last_modified = max(p.stat().st_mtime for p in pages)
                            site_info["last_updated"] = datetime.fromtimestamp(last_modified).isoformat()
            
            # Check for site manifest
            manifest_path = site_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    site_info["name"] = manifest.get("name", site_dir.name)
                    site_info["base_url"] = manifest.get("base_url", "")
            
            sites.append(site_info)
        
        return sites
    
    async def refresh_content(
        self,
        site: str,
        pages: Optional[List[str]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Refresh content for specific sites or pages
        
        Args:
            site: Site slug to refresh
            pages: Optional list of pages to refresh
            force: Force refresh even if unchanged
        
        Returns:
            Refresh results
        """
        logger.info(f"Refreshing content for site: {site}")
        
        results = {
            "site": site,
            "refreshed": [],
            "skipped": [],
            "errors": []
        }
        
        # Load site configuration
        config_path = self.base_path / "config" / "targets.yaml"
        if not config_path.exists():
            return {
                "status": "error",
                "error": "Configuration file not found"
            }
        
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Find site configuration
        site_config = None
        for s in config.get("sites", []):
            if s["slug"] == site:
                site_config = s
                break
        
        if not site_config:
            return {
                "status": "error",
                "error": f"Site not found in configuration: {site}"
            }
        
        # Determine pages to refresh
        if pages:
            urls = []
            for page in pages:
                # Find matching page URL
                for p in site_config.get("pages", []):
                    if page in p["path"]:
                        urls.append(site_config["base_url"] + p["path"])
                        break
        else:
            # Refresh all pages
            urls = [
                site_config["base_url"] + p["path"]
                for p in site_config.get("pages", [])
            ]
        
        # Refresh each page
        for url in urls:
            try:
                result = await self.fetch_page(url, cache=not force)
                
                if result["status"] == "success":
                    results["refreshed"].append(url)
                elif result["status"] == "cached" and not force:
                    results["skipped"].append(url)
                else:
                    results["errors"].append({
                        "url": url,
                        "error": result.get("error", "Unknown error")
                    })
            
            except Exception as e:
                logger.error(f"Error refreshing {url}: {e}")
                results["errors"].append({
                    "url": url,
                    "error": str(e)
                })
        
        return results
    
    async def optimize_markdown(
        self,
        content: str,
        source_url: Optional[str] = None,
        optimization_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Optimize raw markdown for MCP consumption
        
        Args:
            content: Raw markdown content
            source_url: Optional source URL
            optimization_level: Level of optimization
        
        Returns:
            Optimized MCP content
        """
        from ..core.mcp_optimizer import optimize_for{source-slug}
        
        try:
            # Apply optimization
            optimized = optimize_for{source-slug}(
                content,
                source_url or "manual",
                level=optimization_level
            )
            
            return {
                "status": "success",
                "original_size": len(content),
                "optimized_size": len(yaml.dump(optimized)),
                "compression_ratio": f"{(1 - len(yaml.dump(optimized)) / len(content)) * 100:.1f}%",
                "content": optimized
            }
        
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Helper methods
    
    def _extract_site_slug(self, url: str) -> str:
        """Extract site slug from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain.replace(".", "-")
    
    def _extract_page_slug(self, url: str) -> str:
        """Extract page slug from URL"""
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if not path:
            return "index"
        # Convert path to slug
        return path.replace("/", "-").replace(".", "-")
    
    async def _check_cache(self, site: str, page: str) -> Optional[Dict]:
        """Check if content is cached and recent"""
        mcp_path = self.context_dir / site / "pages" / f"{page}.mdc"
        raw_path = self.raw_dir / site / "latest" / f"{page}.md"
        
        if mcp_path.exists() and raw_path.exists():
            # Check age (cache for 24 hours by default)
            age = datetime.now().timestamp() - mcp_path.stat().st_mtime
            if age < 86400:  # 24 hours
                return {
                    "raw_path": raw_path,
                    "mcp_path": mcp_path,
                    "cached_at": datetime.fromtimestamp(mcp_path.stat().st_mtime).isoformat()
                }
        
        return None
    
    def _extract_searchable_text(self, mcp_content: Dict) -> str:
        """Extract searchable text from MCP content"""
        text_parts = []
        
        # Add title
        if "content" in mcp_content:
            content = mcp_content["content"]
            if "title" in content:
                text_parts.append(content["title"])
            
            # Add sections
            if "sections" in content:
                for section in content["sections"]:
                    if "heading" in section:
                        text_parts.append(section["heading"])
                    if "content" in section:
                        text_parts.append(section["content"])
        
        # Add context topics
        if "context" in mcp_content:
            context = mcp_content["context"]
            if "topics" in context:
                text_parts.extend(context["topics"])
        
        return " ".join(text_parts)
    
    def _extract_preview(self, text: str, query: str, context_chars: int = 100) -> str:
        """Extract preview snippet around query match"""
        lower_text = text.lower()
        lower_query = query.lower()
        
        pos = lower_text.find(lower_query)
        if pos == -1:
            return text[:200] + "..." if len(text) > 200 else text
        
        # Extract context around match
        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(query) + context_chars)
        
        preview = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            preview = "..." + preview
        if end < len(text):
            preview = preview + "..."
        
        return preview
    
    async def _update_site_index(self, site: str, page: str, metadata: Dict):
        """Update site index with new page information"""
        index_path = self.context_dir / site / "index.json"
        
        # Load existing index or create new
        if index_path.exists():
            with open(index_path) as f:
                index = json.load(f)
        else:
            index = {
                "site": site,
                "pages": {},
                "last_updated": None
            }
        
        # Update page entry
        index["pages"][page] = {
            "url": metadata["url"],
            "fetched_at": metadata["fetched_at"],
            "content_hash": metadata["content_hash"],
            "word_count": metadata["word_count"]
        }
        
        index["last_updated"] = datetime.now().isoformat()
        
        # Save index
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
