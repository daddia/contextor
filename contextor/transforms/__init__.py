"""Content transformation pipeline for Contextor."""

from __future__ import annotations

from .links import fix_links
from .markdown_norm import normalize_markdown
from .mdx_clean import clean_mdx
from .size import compress_content

__all__ = ["apply_transforms", "clean_mdx", "normalize_markdown", "fix_links", "compress_content"]


def apply_transforms(
    content: str,
    profile: str = "balanced",
    source_path: str = "",
) -> str:
    """Apply the full transformation pipeline to content.

    Args:
        content: Raw content to transform
        profile: Optimization profile (lossless, balanced, compact)
        source_path: Source file path for context

    Returns:
        Transformed content
    """
    # Phase 1: Clean MDX syntax
    content = clean_mdx(content)

    # Phase 2: Normalize Markdown
    content = normalize_markdown(content)

    # Phase 3: Fix links
    content = fix_links(content, source_path)

    # Phase 4: Size optimization (based on profile)
    if profile in ["balanced", "compact"]:
        content = compress_content(content, aggressive=(profile == "compact"))

    return content
