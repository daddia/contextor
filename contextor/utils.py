"""Utility functions for Contextor."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Input text to slugify

    Returns:
        Slugified text with only alphanumeric characters, hyphens, and underscores
    """
    # Convert to lowercase and replace special chars with hyphens, preserve dots temporarily
    slug = re.sub(r"[^\w\s.-]", "-", text.lower())
    # Replace dots with hyphens (except between digits)
    slug = re.sub(r"\.(?!\d)", "-", slug)
    slug = re.sub(r"(?<!\d)\.", "-", slug)
    # Replace multiple hyphens/spaces with single hyphen
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def content_hash(content: str) -> str:
    """Generate SHA-256 hash of content for change detection.

    Args:
        content: Content to hash

    Returns:
        Hexadecimal SHA-256 hash string
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def path_to_slug(path: str | Path, source: str) -> str:
    """Convert a file path to a deterministic slug.

    Args:
        path: File path (relative to source directory)
        source: Source identifier (e.g., repo name)

    Returns:
        Deterministic slug in format: {source}__{path-with-__-separators}
    """
    path_str = str(path)
    # Replace path separators and dots with double underscores
    path_slug = path_str.replace("/", "__").replace(".", "__")
    # Remove file extension from the end
    if path_slug.endswith("__md") or path_slug.endswith("__mdx"):
        path_slug = path_slug.rsplit("__", 1)[0]

    source_slug = slugify(source)
    return f"{source_slug}__{path_slug}"


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure

    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
