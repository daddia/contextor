"""Content size optimization transforms."""

import re


def compress_content(content: str, aggressive: bool = False) -> str:
    """Apply size optimization to content.

    Compresses large code blocks and JSON while preserving meaning.

    Args:
        content: Content to compress
        aggressive: Whether to apply aggressive compression

    Returns:
        Compressed content with clear markers
    """
    # Compress large code blocks
    content = _compress_code_blocks(content, aggressive)

    # Compress large JSON blocks
    content = _compress_json_blocks(content, aggressive)

    # Remove excessive whitespace (but preserve structure)
    if aggressive:
        content = _compress_whitespace(content)

    return content


def _compress_code_blocks(content: str, aggressive: bool) -> str:
    """Compress large code blocks while preserving key information."""

    def compress_block(match):
        fence_start = match.group(1)  # ```language
        code_content = match.group(2)
        fence_end = match.group(3)  # ```

        lines = code_content.split("\n")

        # Only compress if block is large
        threshold = 15 if aggressive else 25
        if len(lines) <= threshold:
            return match.group(0)

        # Keep first few lines, add summary, keep last few lines
        keep_start = 5 if aggressive else 8
        keep_end = 3 if aggressive else 5

        start_lines = lines[:keep_start]
        end_lines = lines[-keep_end:] if keep_end > 0 else []

        # Create summary
        total_lines = len(lines)
        omitted_lines = total_lines - keep_start - keep_end

        summary = f"\n// ... ({omitted_lines} lines omitted for brevity) ...\n"

        compressed_content = "\n".join(start_lines) + summary + "\n".join(end_lines)

        return f"{fence_start}{compressed_content}{fence_end}"

    # Match code blocks
    pattern = r"(```[\w+-]*\n)(.*?)(```)"
    return re.sub(pattern, compress_block, content, flags=re.DOTALL)


def _compress_json_blocks(content: str, aggressive: bool) -> str:
    """Compress large JSON blocks in code fences."""

    def compress_json(match):
        fence_start = match.group(1)
        json_content = match.group(2)
        fence_end = match.group(3)

        # Check if this looks like JSON
        json_content_stripped = json_content.strip()
        if not (
            json_content_stripped.startswith(("{", "["))
            and json_content_stripped.endswith(("}", "]"))
        ):
            return match.group(0)

        lines = json_content.split("\n")
        threshold = 10 if aggressive else 20

        if len(lines) <= threshold:
            return match.group(0)

        # For JSON, show structure but compress content
        # This is a simple implementation - could be more sophisticated
        keep_lines = 6 if aggressive else 10
        start_lines = lines[:keep_lines]

        total_lines = len(lines)
        omitted_lines = total_lines - keep_lines

        summary = f"  // ... ({omitted_lines} more lines) ...\n"
        if json_content_stripped.endswith("}"):
            summary += "}"
        elif json_content_stripped.endswith("]"):
            summary += "]"

        compressed_content = "\n".join(start_lines) + "\n" + summary

        return f"{fence_start}{compressed_content}{fence_end}"

    # Match JSON code blocks
    pattern = r"(```(?:json|jsonc?)\n)(.*?)(```)"
    return re.sub(pattern, compress_json, content, flags=re.DOTALL | re.IGNORECASE)


def _compress_whitespace(content: str) -> str:
    """Compress excessive whitespace while preserving structure."""
    # Limit consecutive blank lines to 2
    content = re.sub(r"\n{4,}", "\n\n\n", content)

    # Remove trailing spaces
    content = re.sub(r"[ \t]+$", "", content, flags=re.MULTILINE)

    return content
