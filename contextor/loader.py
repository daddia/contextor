"""Document loader for discovering and loading Markdown/MDX files."""

from __future__ import annotations

import fnmatch
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter
import structlog
import yaml

logger = structlog.get_logger()


@dataclass
class DocumentInfo:
    """Information about a discovered document."""

    path: str  # Relative path from source directory
    content: str  # Raw content
    title: str | None  # Extracted title
    canonical_url: str | None  # GitHub URL to the file


class DocumentLoader:
    """Loads and discovers Markdown/MDX files from a directory."""

    def __init__(
        self, source_dir: Path, repo: str, ref: str, config_path: Path | None = None
    ):
        """Initialize the document loader.

        Args:
            source_dir: Source directory to scan
            repo: Repository identifier (e.g., 'vercel/next.js')
            ref: Git reference (branch or commit SHA)
            config_path: Optional configuration file path
        """
        self.source_dir = Path(source_dir)
        self.repo = repo
        self.ref = ref
        self.config = self._load_config(config_path)

        # Default patterns
        self.include_patterns = self.config.get(
            "include", ["*.md", "*.mdx", "**/*.md", "**/*.mdx"]
        )
        self.exclude_patterns = self.config.get(
            "exclude",
            [
                "node_modules/*",
                "node_modules/**/*",
                ".git/*",
                ".git/**/*",
                "dist/*",
                "dist/**/*",
                "build/*",
                "build/**/*",
            ],
        )

    def _load_config(self, config_path: Path | None) -> dict[str, Any]:
        """Load configuration from YAML file."""
        if not config_path or not config_path.exists():
            return {}

        try:
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning("Failed to load config", path=config_path, error=str(e))
            return {}

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included based on patterns."""
        relative_path = file_path.relative_to(self.source_dir)
        path_str = str(relative_path)

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(path_str, pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
            if relative_path.match(pattern):
                return True

        return False

    def _extract_title(self, content: str, file_path: str) -> str | None:
        """Extract title from content (frontmatter or first heading)."""
        try:
            # Try to parse frontmatter
            post = frontmatter.loads(content)
            if post.metadata.get("title"):
                return post.metadata["title"]
        except Exception:
            pass

        # Look for first heading
        lines = content.split("\n")
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()

        # Fall back to filename
        return Path(file_path).stem.replace("-", " ").replace("_", " ").title()

    def _build_canonical_url(self, relative_path: str) -> str:
        """Build canonical URL for a file."""
        # Handle GitHub URLs (most common case)
        if "/" in self.repo and not self.repo.startswith(("http://", "https://")):
            return f"https://github.com/{self.repo}/blob/{self.ref}/{relative_path}"

        # For other repos or full URLs, return a generic format
        return f"{self.repo}/{self.ref}/{relative_path}"

    def discover_files(self) -> Iterator[DocumentInfo]:
        """Discover and yield document information for all matching files."""
        if not self.source_dir.exists():
            logger.error("Source directory does not exist", path=self.source_dir)
            return

        # Find all Markdown/MDX files
        for file_path in self.source_dir.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in [".md", ".mdx"]:
                continue

            if not self._should_include_file(file_path):
                continue

            try:
                # Read file content
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Get relative path
                relative_path = str(file_path.relative_to(self.source_dir))

                # Extract title
                title = self._extract_title(content, relative_path)

                # Build canonical URL
                canonical_url = self._build_canonical_url(relative_path)

                yield DocumentInfo(
                    path=relative_path,
                    content=content,
                    title=title,
                    canonical_url=canonical_url,
                )

            except Exception as e:
                logger.error("Failed to read file", path=file_path, error=str(e))
