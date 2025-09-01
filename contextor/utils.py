"""Utility functions for Contextor."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for
        encoding_name: Tiktoken encoding to use (cl100k_base for GPT-3.5/4)

    Returns:
        Number of tokens

    Note:
        Falls back to word-based estimation if tiktoken is not available.
    """
    try:
        import tiktoken

        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except ImportError:
        # Fallback to word-based estimation
        return estimate_tokens_from_words(text)


def estimate_tokens_from_words(text: str) -> int:
    """Estimate token count from word count using the 4/3 ratio.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated number of tokens (words * 4/3)
    """
    words = len(text.split())
    return int(words * 4 / 3)  # 1 token ≈ 3/4 words


def estimate_tokens_from_chars(text: str) -> int:
    """Estimate token count from character count using the 1/4 ratio.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated number of tokens (chars / 4)
    """
    return len(text) // 4  # 1 token ≈ 4 characters


def get_content_stats(text: str) -> dict[str, Any]:
    """Get comprehensive content statistics.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with content statistics
    """
    lines = text.splitlines()
    words = text.split()
    chars = len(text)
    chars_no_spaces = len(text.replace(" ", ""))

    # Count different types of content
    code_blocks = len(re.findall(r"```[\s\S]*?```", text))
    inline_code = len(re.findall(r"`[^`]+`", text))
    links = len(re.findall(r"\[([^\]]+)\]\([^\)]+\)", text))
    headings = len(re.findall(r"^#+\s", text, re.MULTILINE))

    return {
        "lines": len(lines),
        "words": len(words),
        "characters": chars,
        "characters_no_spaces": chars_no_spaces,
        "tokens": count_tokens(text),
        "tokens_estimated_words": estimate_tokens_from_words(text),
        "tokens_estimated_chars": estimate_tokens_from_chars(text),
        "code_blocks": code_blocks,
        "inline_code": inline_code,
        "links": links,
        "headings": headings,
        "avg_words_per_line": len(words) / max(1, len(lines)),
        "avg_chars_per_word": chars / max(1, len(words)),
    }


def format_size(size_bytes: int) -> str:
    """Format byte size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024:
            return f"{size_float:.1f} {unit}"
        size_float /= 1024
    return f"{size_float:.1f} TB"


def format_number(num: int) -> str:
    """Format large numbers with commas.

    Args:
        num: Number to format

    Returns:
        Formatted number string
    """
    return f"{num:,}"


def content_hash(content: str) -> str:
    """Generate SHA-256 hash of content.

    Args:
        content: Content to hash

    Returns:
        Hex digest of SHA-256 hash
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def slugify(text: str) -> str:
    """Convert text to URL-safe slug.

    Args:
        text: Text to slugify

    Returns:
        URL-safe slug
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def path_to_slug(file_path: str, source: str = "") -> str:
    """Convert file path to consistent slug.

    Args:
        file_path: File path to convert
        source: Source identifier to prepend

    Returns:
        Consistent slug for the file
    """
    path = Path(file_path)

    # Remove extension
    name_without_ext = path.stem

    # Get directory parts
    parts = list(path.parent.parts) if path.parent != Path(".") else []

    # Add filename
    parts.append(name_without_ext)

    # Create slug from all parts
    if source:
        all_parts = [slugify(source)] + [slugify(part) for part in parts]
    else:
        all_parts = [slugify(part) for part in parts]

    return "__".join(all_parts)


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)
