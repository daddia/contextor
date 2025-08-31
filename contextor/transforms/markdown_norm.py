"""Markdown normalization transforms."""

import re
from typing import Any

import mdformat


def normalize_markdown(content: str) -> str:
    """Normalize Markdown content using mdformat.

    Standardizes headings, code fences, tables, and spacing.

    Args:
        content: Raw Markdown content

    Returns:
        Normalized Markdown content
    """
    try:
        # Use mdformat with GFM support for normalization
        normalized = mdformat.text(
            content,
            options={
                "wrap": "no",  # Don't wrap lines
                "number": False,  # Don't number lists
            },
            extensions={"gfm"},  # GitHub Flavored Markdown
        )

        # Additional custom normalizations
        normalized = _normalize_headings(normalized)
        normalized = _normalize_code_fences(normalized)
        normalized = _normalize_spacing(normalized)

        return normalized

    except Exception:
        # Fall back to basic normalizations if mdformat fails
        content = _normalize_headings(content)
        content = _normalize_code_fences(content)
        content = _normalize_spacing(content)
        return content


def _normalize_headings(content: str) -> str:
    """Normalize heading syntax to use # style consistently."""
    lines = content.split("\n")
    normalized_lines: list[str] = []

    for i, line in enumerate(lines):
        # Convert underline-style headings to # style
        if i > 0 and line.strip() and all(c in "=-" for c in line.strip()):
            prev_line = lines[i - 1].strip()
            if prev_line:
                # Remove the previous line from results and replace with heading
                normalized_lines.pop()
                if "=" in line:
                    normalized_lines.append(f"# {prev_line}")
                else:
                    normalized_lines.append(f"## {prev_line}")
                continue

        # Normalize # headings (ensure single space after #)
        heading_match = re.match(r"^(#+)\s*(.*)", line)
        if heading_match:
            hashes, title = heading_match.groups()
            normalized_lines.append(f"{hashes} {title.strip()}")
        else:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)


def _normalize_code_fences(content: str) -> str:
    """Normalize code fence syntax."""
    # Standardize code fences to use ``` (not ~~~)
    content = re.sub(r"^~~~(\w*)", r"```\1", content, flags=re.MULTILINE)
    content = re.sub(r"^~~~\s*$", r"```", content, flags=re.MULTILINE)

    # Ensure language specifiers are lowercase
    def normalize_lang(match: Any) -> str:
        fence, lang, rest = match.groups()
        if lang:
            lang = lang.lower()
        return f"{fence}{lang or ''}{rest}"

    content = re.sub(
        r"^(```)([\w+-]*)(.*?)$", normalize_lang, content, flags=re.MULTILINE
    )

    return content


def _normalize_spacing(content: str) -> str:
    """Normalize spacing and line breaks."""
    # Remove trailing whitespace
    content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)

    # Normalize multiple blank lines to at most 2
    content = re.sub(r"\n{4,}", "\n\n\n", content)

    # Ensure single trailing newline
    content = content.rstrip("\n") + "\n"

    return content
