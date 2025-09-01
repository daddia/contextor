"""Document loader for discovering and loading Markdown/MDX files."""

from __future__ import annotations

import fnmatch
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frontmatter
import structlog

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
        self, source_dir: Path, repo: str, ref: str, project_config: Any = None
    ):
        """Initialize the document loader.

        Args:
            source_dir: Source directory to scan
            repo: Repository identifier (e.g., 'vercel/next.js')
            ref: Git reference (branch or commit SHA)
            project_config: Optional project configuration object
        """
        self.source_dir = Path(source_dir)
        self.repo = repo
        self.ref = ref
        self.project_config = project_config

        # Use project config or defaults
        if project_config:
            self.config = project_config.to_legacy_format()
            # When processing a specific folder from the config, adjust patterns
            self._adjust_patterns_for_folder()
        else:
            self.config = {}

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

    def _adjust_patterns_for_folder(self) -> None:
        """Adjust include/exclude patterns when processing a specific configured folder."""
        if not self.project_config or not self.project_config.folders:
            return

        # Check if our source directory matches any configured folder
        source_parts = self.source_dir.parts

        for folder in self.project_config.folders:
            folder_parts = Path(folder).parts

            # Check if source directory ends with the configured folder path
            if len(source_parts) >= len(folder_parts):
                if source_parts[-len(folder_parts) :] == folder_parts:
                    # We're processing this specific folder, so use simple patterns
                    self.config["include"] = ["*.md", "*.mdx", "**/*.md", "**/*.mdx"]
                    logger.debug(
                        "Adjusted patterns for folder",
                        folder=folder,
                        source=self.source_dir,
                    )
                    return

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included based on patterns."""
        relative_path = file_path.relative_to(self.source_dir)
        path_str = str(relative_path)

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if self._matches_pattern(path_str, pattern):
                return False

        # Check include patterns
        for pattern in self.include_patterns:
            if self._matches_pattern(path_str, pattern):
                return True

        return False

    def _matches_pattern(self, path_str: str, pattern: str) -> bool:
        """Check if a path matches a glob pattern, supporting ** wildcards."""
        # Use pathlib for patterns with **
        if "**" in pattern:
            try:
                # Convert to Path and use match
                path_obj = Path(path_str)
                return path_obj.match(pattern)
            except Exception:
                # Fallback to fnmatch if Path.match fails
                return fnmatch.fnmatch(path_str, pattern)
        else:
            # Use fnmatch for simple patterns
            return fnmatch.fnmatch(path_str, pattern)

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
