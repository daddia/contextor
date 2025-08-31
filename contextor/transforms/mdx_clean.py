"""MDX cleaning transforms."""

import re


def clean_mdx(content: str) -> str:
    """Clean MDX-specific syntax from content.

    Removes import/export statements and unwraps common JSX components
    while preserving content semantics.

    Args:
        content: Raw MDX content

    Returns:
        Cleaned content with MDX syntax removed
    """
    lines = content.split('\n')
    cleaned_lines = []
    in_frontmatter = False
    frontmatter_delim_count = 0

    for line in lines:
        # Track frontmatter boundaries
        if line.strip() == '---':
            frontmatter_delim_count += 1
            if frontmatter_delim_count <= 2:
                cleaned_lines.append(line)
                continue

        # Skip frontmatter processing
        if frontmatter_delim_count == 1:
            cleaned_lines.append(line)
            continue
        elif frontmatter_delim_count == 2 and not in_frontmatter:
            in_frontmatter = True

        # Remove import statements
        if re.match(r'^\s*import\s+', line):
            continue

        # Remove export statements (but keep export default for content)
        if re.match(r'^\s*export\s+(?!default)', line):
            continue

        # Clean common JSX wrappers
        cleaned_line = _unwrap_jsx_components(line)
        cleaned_lines.append(cleaned_line)

    return '\n'.join(cleaned_lines)


def _unwrap_jsx_components(line: str) -> str:
    """Unwrap common JSX components while preserving content."""

    # Common component patterns to unwrap
    patterns = [
        # <Callout type="info">content</Callout> -> content
        (r'<Callout[^>]*>(.*?)</Callout>', r'\1'),

        # <Note>content</Note> -> content
        (r'<Note[^>]*>(.*?)</Note>', r'\1'),

        # <Warning>content</Warning> -> content
        (r'<Warning[^>]*>(.*?)</Warning>', r'\1'),

        # <Details summary="title">content</Details> -> content
        (r'<Details[^>]*>(.*?)</Details>', r'\1'),

        # Self-closing components - remove entirely
        (r'<[A-Z][a-zA-Z0-9]*[^>]*\s*/>', ''),

        # Simple wrapper components
        (r'<([A-Z][a-zA-Z0-9]*)[^>]*>(.*?)</\1>', r'\2'),
    ]

    cleaned = line
    for pattern, replacement in patterns:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    return cleaned
