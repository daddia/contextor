"""MDC file emission and manifest management."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import frontmatter
import structlog

from .utils import content_hash, ensure_directory, get_content_stats, path_to_slug

logger = structlog.get_logger()


class MDCEmitter:
    """Emits .mdc files and maintains index.jsonl manifest."""

    def __init__(self, output_dir: Path):
        """Initialize the MDC emitter.

        Args:
            output_dir: Output directory for .mdc files
        """
        self.output_dir = Path(output_dir)
        self.index_path = self.output_dir / "index.jsonl"

        # Track cumulative statistics
        self.cumulative_stats = {
            "files": 0,
            "lines": 0,
            "words": 0,
            "characters": 0,
            "tokens": 0,
            "tokens_estimated_words": 0,
            "tokens_estimated_chars": 0,
            "code_blocks": 0,
            "inline_code": 0,
            "links": 0,
            "headings": 0,
            "size_bytes": 0,
        }

        # Ensure output directory exists
        ensure_directory(self.output_dir)

    def emit_mdc(self, content: str, metadata: dict[str, Any]) -> bool:
        """Emit a .mdc file with front-matter and content.

        Args:
            content: Processed content to emit
            metadata: Metadata dict with repo, ref, path, url, title, topics

        Returns:
            True if file was written, False if skipped (no changes)
        """
        # Generate content hash
        current_hash = content_hash(content)

        # Generate slug for filename
        source = metadata.get("repo", "unknown").split("/")[-1]  # Get repo name
        slug = path_to_slug(metadata.get("path", "unknown"), source)

        # Analyze content for token statistics
        content_stats = get_content_stats(content)

        # Build full front-matter
        frontmatter = {
            "schema": "mdc/1.0",
            "source": {
                "repo": metadata.get("repo"),
                "ref": metadata.get("ref"),
                "path": metadata.get("path"),
                "url": metadata.get("url"),
            },
            "title": metadata.get("title"),
            "topics": metadata.get("topics", []),
            "content_hash": current_hash,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "slug": slug,
            "license": "See source repository",
            "stats": {
                "lines": content_stats["lines"],
                "words": content_stats["words"],
                "characters": content_stats["characters"],
                "tokens": content_stats["tokens"],
                "tokens_estimated_words": content_stats["tokens_estimated_words"],
                "tokens_estimated_chars": content_stats["tokens_estimated_chars"],
                "code_blocks": content_stats["code_blocks"],
                "inline_code": content_stats["inline_code"],
                "links": content_stats["links"],
                "headings": content_stats["headings"],
            },
        }

        # Check if we need to write (compare hash with existing file)
        mdc_path = self.output_dir / f"{slug}.mdc"
        if self._should_skip_write(mdc_path, current_hash):
            logger.debug(
                "Skipping unchanged file", slug=slug, path=metadata.get("path")
            )
            return False

        # Calculate content size in bytes
        content_size_bytes = len(content.encode("utf-8"))

        # Update cumulative statistics
        self._update_cumulative_stats(content_stats, content_size_bytes)

        # Write .mdc file
        self._write_mdc_file(mdc_path, frontmatter, content)

        # Update index
        self._update_index(slug, frontmatter)

        logger.info("Emitted .mdc file", slug=slug, path=metadata.get("path"))
        return True

    def _should_skip_write(self, mdc_path: Path, current_hash: str) -> bool:
        """Check if we should skip writing based on content hash."""
        if not mdc_path.exists():
            return False

        try:
            # Read existing file and parse frontmatter
            with open(mdc_path, encoding="utf-8") as f:
                post = frontmatter.load(f)

            # Check if hash matches
            existing_hash = post.metadata.get("content_hash")
            if existing_hash == current_hash:
                return True

        except Exception as e:
            logger.warning("Failed to read existing file", path=mdc_path, error=str(e))

        return False

    def _write_mdc_file(
        self, path: Path, frontmatter: dict[str, Any], content: str
    ) -> None:
        """Write .mdc file with YAML frontmatter and content."""

        # Build YAML frontmatter
        yaml_lines = ["---"]
        yaml_lines.extend(self._dict_to_yaml(frontmatter, indent=0))
        yaml_lines.append("---")
        yaml_lines.append("")  # Empty line after frontmatter

        # Combine frontmatter and content
        full_content = "\n".join(yaml_lines) + content

        # Write file
        with open(path, "w", encoding="utf-8") as f:
            f.write(full_content)

    def _dict_to_yaml(self, data: Any, indent: int = 0) -> list[str]:
        """Convert dictionary to YAML lines (simple implementation)."""
        lines = []
        indent_str = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{indent_str}{key}:")
                    lines.extend(self._dict_to_yaml(value, indent + 1))
                elif isinstance(value, list):
                    lines.append(f"{indent_str}{key}:")
                    for item in value:
                        if isinstance(item, str):
                            lines.append(f"{indent_str}  - {json.dumps(item)}")
                        else:
                            lines.append(f"{indent_str}  - {item}")
                elif isinstance(value, str):
                    lines.append(f"{indent_str}{key}: {json.dumps(value)}")
                else:
                    lines.append(f"{indent_str}{key}: {value}")

        return lines

    def _update_index(self, slug: str, frontmatter: dict[str, Any]) -> None:
        """Update the index.jsonl manifest file."""

        # Create index entry with token statistics
        index_entry = {
            "slug": slug,
            "title": frontmatter.get("title"),
            "path": frontmatter.get("source", {}).get("path"),
            "repo": frontmatter.get("source", {}).get("repo"),
            "ref": frontmatter.get("source", {}).get("ref"),
            "topics": frontmatter.get("topics", []),
            "content_hash": frontmatter.get("content_hash"),
            "fetched_at": frontmatter.get("fetched_at"),
            "stats": frontmatter.get("stats", {}),
        }

        # Read existing index entries
        existing_entries = []
        if self.index_path.exists():
            try:
                with open(self.index_path, encoding="utf-8") as f:
                    existing_entries = [
                        json.loads(line.strip()) for line in f if line.strip()
                    ]
            except Exception as e:
                logger.warning("Failed to read existing index", error=str(e))

        # Remove existing entry for this slug
        existing_entries = [e for e in existing_entries if e.get("slug") != slug]

        # Add new entry
        existing_entries.append(index_entry)

        # Write updated index
        with open(self.index_path, "w", encoding="utf-8") as f:
            for entry in existing_entries:
                f.write(json.dumps(entry) + "\n")

    def _update_cumulative_stats(
        self, content_stats: dict[str, Any], size_bytes: int
    ) -> None:
        """Update cumulative statistics with content from a single file."""
        self.cumulative_stats["files"] += 1
        self.cumulative_stats["size_bytes"] += size_bytes

        for key in [
            "lines",
            "words",
            "characters",
            "tokens",
            "tokens_estimated_words",
            "tokens_estimated_chars",
            "code_blocks",
            "inline_code",
            "links",
            "headings",
        ]:
            if key in content_stats and content_stats[key] is not None:
                self.cumulative_stats[key] += content_stats[key]

    def finalize_stats(self) -> dict[str, Any]:
        """Finalize and return cumulative statistics.

        Returns:
            The final statistics dictionary
        """
        # Calculate averages
        if self.cumulative_stats["files"] > 0:
            averages = {
                "tokens_per_file": self.cumulative_stats["tokens"]
                / self.cumulative_stats["files"],
                "words_per_file": self.cumulative_stats["words"]
                / self.cumulative_stats["files"],
                "lines_per_file": self.cumulative_stats["lines"]
                / self.cumulative_stats["files"],
                "chars_per_file": self.cumulative_stats["characters"]
                / self.cumulative_stats["files"],
                "size_per_file": self.cumulative_stats["size_bytes"]
                / self.cumulative_stats["files"],
            }
        else:
            averages = {}

        # Build final stats
        final_stats = {
            "summary": self.cumulative_stats.copy(),
            "averages": averages,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

        logger.info(
            "Finalized processing stats",
            files=self.cumulative_stats["files"],
            tokens=self.cumulative_stats["tokens"],
        )
        return final_stats
