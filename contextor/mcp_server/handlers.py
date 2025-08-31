"""
Request handlers for Contextor MCP Server - Updated for sourcedocs serving
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class SourceDocsHandlers:
    """
    Handles MCP tool invocations for serving sourcedocs content
    """

    def __init__(self, sourcedocs_path: Path):
        """
        Initialize handlers with sourcedocs directory path

        Args:
            sourcedocs_path: Path to the sourcedocs directory
        """
        self.sourcedocs_path = sourcedocs_path.resolve()

        if not self.sourcedocs_path.exists():
            raise ValueError(f"Sourcedocs path does not exist: {self.sourcedocs_path}")

        logger.info(
            f"Handlers initialized with sourcedocs path: {self.sourcedocs_path}"
        )

    async def list_source(
        self,
        source_slug: str | None = None,
        since: str | None = None,
        include_stats: bool = False,
    ) -> dict[str, Any]:
        """
        List available source slugs and their content structure

        Args:
            source_slug: Optional source slug for detailed listing
            since: Optional ISO timestamp to filter by modification time
            include_stats: Whether to include file statistics

        Returns:
            Dictionary with source listings
        """
        logger.info(f"Listing sources: {source_slug}, since: {since}")

        try:
            since_timestamp = None
            if since:
                try:
                    since_timestamp = datetime.fromisoformat(
                        since.replace("Z", "+00:00")
                    ).timestamp()
                except ValueError:
                    logger.warning(f"Invalid timestamp format: {since}")

            if source_slug:
                # List specific source
                source_path = self.sourcedocs_path / source_slug
                if not source_path.exists():
                    return {
                        "status": "not_found",
                        "error": f"Source not found: {source_slug}",
                    }

                return await self._list_source_detailed(
                    source_path, source_slug, since_timestamp, include_stats
                )

            else:
                # List all sources
                sources = []

                for item in self.sourcedocs_path.iterdir():
                    if item.is_dir() and not item.name.startswith("."):
                        source_info = {
                            "slug": item.name,
                            "path": str(item.relative_to(self.sourcedocs_path)),
                        }

                        if include_stats:
                            stats = await self._get_source_stats(item, since_timestamp)
                            source_info.update(stats)

                        sources.append(source_info)

                return {
                    "status": "success",
                    "sources": sources,
                    "total_sources": len(sources),
                }

        except Exception as e:
            logger.error(f"Error listing sources: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def get_file(
        self, path: str | None = None, slug: str | None = None
    ) -> dict[str, Any]:
        """
        Retrieve a specific file by path or slug

        Args:
            path: File path relative to sourcedocs/
            slug: Alternative file slug identifier

        Returns:
            File content and metadata
        """
        if not path and not slug:
            return {"status": "error", "error": "Either path or slug must be provided"}

        try:
            if path:
                file_path = self.sourcedocs_path / path
            elif slug:
                # Convert slug to path (basic implementation)
                file_path = self._slug_to_path(slug)
            else:
                return {
                    "status": "error",
                    "error": "Either path or slug must be provided",
                }

            if not file_path.exists():
                return {
                    "status": "not_found",
                    "error": f"File not found: {path or slug}",
                }

            if not file_path.is_file():
                return {
                    "status": "error",
                    "error": f"Path is not a file: {path or slug}",
                }

            # Read file content
            content = file_path.read_text(encoding="utf-8")

            # Get file stats
            stat = file_path.stat()

            return {
                "status": "success",
                "path": str(file_path.relative_to(self.sourcedocs_path)),
                "content": content,
                "metadata": {
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "encoding": "utf-8",
                    "line_count": len(content.splitlines()),
                    "word_count": len(content.split()),
                },
            }

        except Exception as e:
            logger.error(f"Error getting file: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def search(
        self,
        query: str,
        source_filter: str | None = None,
        limit: int = 10,
        include_content: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search through sourcedocs content

        Args:
            query: Search query string
            source_filter: Optional source slug to filter by
            limit: Maximum number of results
            include_content: Whether to include content snippets

        Returns:
            List of search results
        """
        logger.info(f"Searching for: '{query}' in source: {source_filter}")

        try:
            results = []
            search_path = (
                self.sourcedocs_path / source_filter
                if source_filter
                else self.sourcedocs_path
            )

            if not search_path.exists():
                return []

            # Search through markdown files
            for file_path in search_path.rglob("*.md"):
                try:
                    content = file_path.read_text(encoding="utf-8")

                    # Simple case-insensitive search
                    if query.lower() in content.lower():
                        # Calculate relevance score (simple count)
                        score = content.lower().count(query.lower())

                        result = {
                            "path": str(file_path.relative_to(self.sourcedocs_path)),
                            "score": score,
                            "source": file_path.parts[len(self.sourcedocs_path.parts)],
                        }

                        if include_content:
                            # Extract preview snippet
                            preview = self._extract_preview(content, query)
                            result["preview"] = preview

                        # Get file metadata
                        stat = file_path.stat()
                        result["metadata"] = {
                            "size": stat.st_size,
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                        }

                        results.append(result)

                except Exception as e:
                    logger.warning(f"Error searching file {file_path}: {e}")
                    continue

            # Sort by relevance score and limit
            def get_score(x: dict[str, Any]) -> float:
                score = x.get("score", 0)
                return float(score) if score is not None else 0.0

            results.sort(key=get_score, reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error searching: {e}", exc_info=True)
            return []

    async def stats(self, detailed: bool = False) -> dict[str, Any]:
        """
        Get statistics about the sourcedocs repository

        Args:
            detailed: Whether to include detailed per-source statistics

        Returns:
            Repository statistics
        """
        logger.info(f"Getting stats, detailed: {detailed}")

        try:
            total_files = 0
            total_size = 0
            total_lines = 0
            total_words = 0
            sources: dict[str, dict[str, Any]] = {}
            file_types: dict[str, int] = {}

            for file_path in self.sourcedocs_path.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    # Count file
                    total_files += 1

                    # Get file stats
                    stat = file_path.stat()
                    total_size += stat.st_size

                    # Count file type
                    suffix = file_path.suffix.lower()
                    file_types[suffix] = file_types.get(suffix, 0) + 1

                    # Get source from path
                    source_name = file_path.parts[len(self.sourcedocs_path.parts)]

                    if detailed:
                        if source_name not in sources:
                            sources[source_name] = {"files": 0, "size": 0, "types": {}}

                        sources[source_name]["files"] += 1
                        sources[source_name]["size"] += stat.st_size
                        sources[source_name]["types"][suffix] = (
                            sources[source_name]["types"].get(suffix, 0) + 1
                        )

                    # Count lines and words for text files
                    if suffix in [".md", ".txt", ".mdx"]:
                        try:
                            content = file_path.read_text(encoding="utf-8")
                            lines = len(content.splitlines())
                            words = len(content.split())

                            total_lines += lines
                            total_words += words

                            if detailed and source_name in sources:
                                if "lines" not in sources[source_name]:
                                    sources[source_name]["lines"] = 0
                                    sources[source_name]["words"] = 0
                                sources[source_name]["lines"] += lines
                                sources[source_name]["words"] += words

                        except Exception:
                            pass  # Skip files that can't be read

            result = {
                "status": "success",
                "total_files": total_files,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "total_lines": total_lines,
                "total_words": total_words,
                "file_types": file_types,
                "generated_at": datetime.now().isoformat(),
            }

            if detailed:
                result["sources"] = sources
            else:
                result["source_count"] = len(
                    {
                        file_path.parts[len(self.sourcedocs_path.parts)]
                        for file_path in self.sourcedocs_path.rglob("*")
                        if file_path.is_file() and not file_path.name.startswith(".")
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    # Helper methods

    async def _list_source_detailed(
        self,
        source_path: Path,
        source_slug: str,
        since_timestamp: float | None,
        include_stats: bool,
    ) -> dict[str, Any]:
        """Get detailed listing for a specific source"""
        files = []

        for file_path in source_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                stat = file_path.stat()

                # Filter by timestamp if provided
                if since_timestamp and stat.st_mtime < since_timestamp:
                    continue

                file_info: dict[str, Any] = {
                    "path": str(file_path.relative_to(self.sourcedocs_path)),
                    "name": file_path.name,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }

                if include_stats:
                    file_info["size"] = stat.st_size

                    # Add content stats for text files
                    if file_path.suffix.lower() in [".md", ".txt", ".mdx"]:
                        try:
                            content = file_path.read_text(encoding="utf-8")
                            file_info["lines"] = len(content.splitlines())
                            file_info["words"] = len(content.split())
                        except Exception:
                            pass

                files.append(file_info)

        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)

        return {
            "status": "success",
            "source": source_slug,
            "files": files,
            "total_files": len(files),
        }

    async def _get_source_stats(
        self, source_path: Path, since_timestamp: float | None
    ) -> dict[str, Any]:
        """Get statistics for a single source"""
        file_count = 0
        total_size = 0
        latest_modified: float | None = None

        for file_path in source_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                stat = file_path.stat()

                # Filter by timestamp if provided
                if since_timestamp and stat.st_mtime < since_timestamp:
                    continue

                file_count += 1
                total_size += stat.st_size

                if latest_modified is None or stat.st_mtime > latest_modified:
                    latest_modified = stat.st_mtime

        stats: dict[str, Any] = {"file_count": file_count, "total_size": total_size}

        if latest_modified:
            stats["last_modified"] = datetime.fromtimestamp(latest_modified).isoformat()

        return stats

    def _slug_to_path(self, slug: str) -> Path:
        """Convert a slug to a file path (basic implementation)"""
        # This is a simple implementation - could be enhanced with a proper slug mapping
        if "/" in slug:
            return self.sourcedocs_path / slug
        else:
            # Search for files matching the slug
            for file_path in self.sourcedocs_path.rglob("*.md"):
                if file_path.stem == slug:
                    return file_path

        # Fallback: treat as direct path
        return self.sourcedocs_path / f"{slug}.md"

    def _extract_preview(
        self, content: str, query: str, context_chars: int = 150
    ) -> str:
        """Extract preview snippet around query match"""
        lower_content = content.lower()
        lower_query = query.lower()

        pos = lower_content.find(lower_query)
        if pos == -1:
            # No exact match, return beginning of content
            return content[:300] + "..." if len(content) > 300 else content

        # Extract context around match
        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)

        preview = content[start:end]

        # Clean up preview (remove incomplete lines at start/end)
        lines = preview.split("\n")
        if len(lines) > 1:
            if start > 0:
                lines = lines[1:]  # Remove potentially incomplete first line
            if end < len(content):
                lines = lines[:-1]  # Remove potentially incomplete last line
            preview = "\n".join(lines)

        # Add ellipsis if truncated
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."

        return preview
