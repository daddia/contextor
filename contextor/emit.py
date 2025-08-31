"""MDC file emission and manifest management."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from .utils import content_hash, ensure_directory, path_to_slug

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
        source = metadata.get('repo', 'unknown').split('/')[-1]  # Get repo name
        slug = path_to_slug(metadata.get('path', 'unknown'), source)

        # Build full front-matter
        frontmatter = {
            "schema": "mdc/1.0",
            "source": {
                "repo": metadata.get('repo'),
                "ref": metadata.get('ref'),
                "path": metadata.get('path'),
                "url": metadata.get('url'),
            },
            "title": metadata.get('title'),
            "topics": metadata.get('topics', []),
            "content_hash": current_hash,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "slug": slug,
            "license": "See source repository",
        }

        # Check if we need to write (compare hash with existing file)
        mdc_path = self.output_dir / f"{slug}.mdc"
        if self._should_skip_write(mdc_path, current_hash):
            logger.debug("Skipping unchanged file", slug=slug, path=metadata.get('path'))
            return False

        # Write .mdc file
        self._write_mdc_file(mdc_path, frontmatter, content)

        # Update index
        self._update_index(slug, frontmatter)

        logger.info("Emitted .mdc file", slug=slug, path=metadata.get('path'))
        return True

    def _should_skip_write(self, mdc_path: Path, current_hash: str) -> bool:
        """Check if we should skip writing based on content hash."""
        if not mdc_path.exists():
            return False

        try:
            # Read existing file and check hash in frontmatter
            with open(mdc_path, encoding='utf-8') as f:
                content = f.read()

            # Extract hash from frontmatter (simple approach)
            if f'content_hash: {current_hash}' in content:
                return True

        except Exception as e:
            logger.warning("Failed to read existing file", path=mdc_path, error=str(e))

        return False

    def _write_mdc_file(self, path: Path, frontmatter: dict[str, Any], content: str) -> None:
        """Write .mdc file with YAML frontmatter and content."""

        # Build YAML frontmatter
        yaml_lines = ["---"]
        yaml_lines.extend(self._dict_to_yaml(frontmatter, indent=0))
        yaml_lines.append("---")
        yaml_lines.append("")  # Empty line after frontmatter

        # Combine frontmatter and content
        full_content = '\n'.join(yaml_lines) + content

        # Write file
        with open(path, 'w', encoding='utf-8') as f:
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

        # Create index entry
        index_entry = {
            "slug": slug,
            "title": frontmatter.get('title'),
            "path": frontmatter.get('source', {}).get('path'),
            "repo": frontmatter.get('source', {}).get('repo'),
            "ref": frontmatter.get('source', {}).get('ref'),
            "topics": frontmatter.get('topics', []),
            "content_hash": frontmatter.get('content_hash'),
            "fetched_at": frontmatter.get('fetched_at'),
        }

        # Read existing index entries
        existing_entries = []
        if self.index_path.exists():
            try:
                with open(self.index_path, encoding='utf-8') as f:
                    existing_entries = [json.loads(line.strip()) for line in f if line.strip()]
            except Exception as e:
                logger.warning("Failed to read existing index", error=str(e))

        # Remove existing entry for this slug
        existing_entries = [e for e in existing_entries if e.get('slug') != slug]

        # Add new entry
        existing_entries.append(index_entry)

        # Write updated index
        with open(self.index_path, 'w', encoding='utf-8') as f:
            for entry in existing_entries:
                f.write(json.dumps(entry) + '\n')
