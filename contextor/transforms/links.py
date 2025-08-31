"""Link processing and hygiene transforms."""

import re
from typing import Any
from urllib.parse import urlparse


def fix_links(content: str, source_path: str = "") -> str:
    """Fix and clean up links in content.

    - Remove "edit this page" boilerplate links
    - Convert relative links to absolute where possible
    - Clean up link formatting

    Args:
        content: Markdown content with links
        source_path: Source file path for resolving relative links

    Returns:
        Content with fixed links
    """
    # Remove common boilerplate links
    content = _remove_boilerplate_links(content)

    # Fix relative links (basic implementation)
    content = _fix_relative_links(content, source_path)

    return content


def _remove_boilerplate_links(content: str) -> str:
    """Remove common boilerplate links."""

    # Patterns for common boilerplate
    boilerplate_patterns = [
        # "Edit this page" links
        r"\[Edit this page[^\]]*\]\([^)]+\)",
        r"\[Edit on GitHub[^\]]*\]\([^)]+\)",
        r"\[Improve this page[^\]]*\]\([^)]+\)",
        # Navigation links that aren't useful in extracted context
        r"\[← Previous[^\]]*\]\([^)]+\)",
        r"\[Next →[^\]]*\]\([^)]+\)",
        r"\[Back to top[^\]]*\]\([^)]+\)",
        # Social/sharing links
        r"\[Share on Twitter[^\]]*\]\([^)]+\)",
        r"\[Share on Facebook[^\]]*\]\([^)]+\)",
    ]

    cleaned = content
    for pattern in boilerplate_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up any double spaces or empty lines left behind
    cleaned = re.sub(r"  +", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned)

    return cleaned


def _fix_relative_links(content: str, source_path: str) -> str:
    """Fix relative links to be more useful in extracted context.

    This is a basic implementation - more sophisticated link resolution
    would require knowledge of the site structure.
    """
    if not source_path:
        return content

    def fix_link(match: Any) -> str:
        link_text = match.group(1)
        link_url = match.group(2)

        # Skip absolute URLs
        if urlparse(link_url).scheme:
            return match.group(0)

        # Skip anchor links
        if link_url.startswith("#"):
            return match.group(0)

        # For relative links, we could try to resolve them
        # For now, we'll just add a comment indicating they're relative
        if link_url.startswith("./") or link_url.startswith("../"):
            return f'[{link_text}]({link_url} "Relative link from {source_path}")'

        return match.group(0)

    # Process markdown links
    content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", fix_link, content)

    return content
