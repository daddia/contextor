"""Tests for content transformation functions."""

from contextor.transforms import apply_transforms
from contextor.transforms.links import (
    _fix_relative_links,
    _remove_boilerplate_links,
    fix_links,
)
from contextor.transforms.markdown_norm import (
    _normalize_code_fences,
    _normalize_headings,
    normalize_markdown,
)
from contextor.transforms.mdx_clean import _unwrap_jsx_components, clean_mdx
from contextor.transforms.size import (
    _compress_code_blocks,
    _compress_json_blocks,
    compress_content,
)


class TestMDXCleaning:
    """Test MDX cleaning functionality."""

    def test_clean_mdx_removes_imports(self):
        """Test that import statements are removed."""
        content = """import { Component } from 'react'
import styles from './styles.css'

# Hello World

Some content here."""

        result = clean_mdx(content)
        assert "import { Component }" not in result
        assert "import styles" not in result
        assert "# Hello World" in result
        assert "Some content here." in result

    def test_clean_mdx_removes_exports(self):
        """Test that export statements are removed (except export default)."""
        content = """export const metadata = { title: 'Test' }
export { someFunction }

# Content

export default function Page() {
  return <div>Hello</div>
}"""

        result = clean_mdx(content)
        assert "export const metadata" not in result
        assert "export { someFunction }" not in result
        assert "# Content" in result
        assert "export default function Page()" in result  # Should be preserved

    def test_clean_mdx_preserves_frontmatter(self):
        """Test that YAML frontmatter is preserved."""
        content = """---
title: Test Page
description: A test page
---

import { Component } from 'react'

# Test Content"""

        result = clean_mdx(content)
        assert "---" in result
        assert "title: Test Page" in result
        assert "description: A test page" in result
        assert "import { Component }" not in result
        assert "# Test Content" in result

    def test_unwrap_jsx_components(self):
        """Test JSX component unwrapping."""
        test_cases = [
            ('<Callout type="info">Important info</Callout>', "Important info"),
            ("<Note>This is a note</Note>", "This is a note"),
            ("<Warning>Be careful</Warning>", "Be careful"),
            ('<Details summary="Click">Hidden content</Details>', "Hidden content"),
            ("<SelfClosing />", ""),
            ("<CustomComponent>Content here</CustomComponent>", "Content here"),
        ]

        for input_text, expected in test_cases:
            result = _unwrap_jsx_components(input_text)
            assert expected in result or expected == result.strip()


class TestMarkdownNormalization:
    """Test Markdown normalization functionality."""

    def test_normalize_headings_hash_style(self):
        """Test heading normalization to # style."""
        content = """#  Heading 1
##   Heading 2
###Heading 3"""

        result = _normalize_headings(content)
        assert "# Heading 1" in result
        assert "## Heading 2" in result
        assert "### Heading 3" in result

    def test_normalize_headings_underline_style(self):
        """Test conversion of underline-style headings."""
        content = """Heading 1
=========

Heading 2
---------

Some content"""

        result = _normalize_headings(content)
        assert "# Heading 1" in result
        assert "## Heading 2" in result
        assert "Some content" in result
        assert "=========" not in result
        assert "---------" not in result

    def test_normalize_code_fences(self):
        """Test code fence normalization."""
        content = """~~~javascript
console.log('hello');
~~~

~~~
plain text
~~~"""

        result = _normalize_code_fences(content)
        assert "```javascript" in result
        assert "```" in result
        assert "~~~" not in result

    def test_normalize_markdown_integration(self):
        """Test full markdown normalization."""
        content = """#  Title

~~~js
code here
~~~

Underlined Heading
==================

Some content."""

        result = normalize_markdown(content)
        assert "# Title" in result
        assert "```js" in result
        assert "# Underlined Heading" in result
        assert "==================" not in result


class TestLinkHygiene:
    """Test link processing functionality."""

    def test_remove_boilerplate_links(self):
        """Test removal of boilerplate links."""
        content = """# Content

[Edit this page](https://github.com/example/repo/edit/main/file.md)
[Edit on GitHub](https://github.com/example/repo/edit/main/file.md)
[← Previous](./prev.md)
[Next →](./next.md)
[Share on Twitter](https://twitter.com/share)

Regular [link](https://example.com) should remain."""

        result = _remove_boilerplate_links(content)
        assert "Edit this page" not in result
        assert "Edit on GitHub" not in result
        assert "← Previous" not in result
        assert "Next →" not in result
        assert "Share on Twitter" not in result
        assert "[link](https://example.com)" in result

    def test_fix_relative_links(self):
        """Test relative link processing."""
        content = """[Relative link](./other-page.md)
[Parent link](../parent.md)
[Absolute link](https://example.com)
[Anchor link](#section)"""

        result = _fix_relative_links(content, "docs/current.md")
        # Relative links should get a comment
        assert "Relative link from docs/current.md" in result
        # Absolute and anchor links should be unchanged
        assert "[Absolute link](https://example.com)" in result
        assert "[Anchor link](#section)" in result

    def test_fix_links_integration(self):
        """Test full link processing."""
        content = """# Page

[Edit this page](https://github.com/example/edit)
[Relative](./other.md)
[Normal](https://example.com)"""

        result = fix_links(content, "docs/page.md")
        assert "Edit this page" not in result
        assert "Relative link from docs/page.md" in result
        assert "[Normal](https://example.com)" in result


class TestSizeCompression:
    """Test content size optimization."""

    def test_compress_code_blocks_small(self):
        """Test that small code blocks are not compressed."""
        content = """```javascript
function small() {
  return 'hello';
}
```"""

        result = _compress_code_blocks(content, aggressive=False)
        assert "lines omitted" not in result
        assert "function small()" in result

    def test_compress_code_blocks_large(self):
        """Test that large code blocks are compressed."""
        # Create a large code block (>25 lines)
        lines = ["const line" + str(i) + ' = "value";' for i in range(30)]
        content = f"```javascript\n{chr(10).join(lines)}\n```"

        result = _compress_code_blocks(content, aggressive=False)
        assert "lines omitted for brevity" in result
        assert "const line0" in result  # Should keep first few lines
        assert "const line29" in result  # Should keep last few lines

    def test_compress_json_blocks(self):
        """Test JSON block compression."""
        # Create a large JSON block (needs to be >20 lines for non-aggressive)
        json_lines = [f'  "key{i}": "value{i}",' for i in range(25)]
        json_content = "{\n" + "\n".join(json_lines) + "\n}"
        content = f"```json\n{json_content}\n```"

        result = _compress_json_blocks(content, aggressive=False)
        assert "more lines" in result
        assert '"key0"' in result  # Should keep first few lines

    def test_compress_content_profiles(self):
        """Test different compression profiles."""
        # Create content with a large code block
        lines = ["const line" + str(i) + ' = "value";' for i in range(30)]
        content = f"# Test\n\n```javascript\n{chr(10).join(lines)}\n```"

        # Lossless should not compress
        lossless = compress_content(content, aggressive=False)
        if len(lines) > 25:  # Only compress if over threshold
            assert "lines omitted" in lossless

        # Aggressive should be more aggressive
        aggressive = compress_content(content, aggressive=True)
        if len(lines) > 15:  # Lower threshold for aggressive
            assert "lines omitted" in aggressive


class TestTransformPipeline:
    """Test the full transformation pipeline."""

    def test_apply_transforms_lossless(self):
        """Test lossless profile preserves all content."""
        content = """---
title: Test
---

import { Component } from 'react'

# Test

<Callout>Important</Callout>

[Edit this page](https://github.com/example/edit)"""

        result = apply_transforms(content, profile="lossless", source_path="test.mdx")

        # Should clean MDX
        assert "import { Component }" not in result

        # Should unwrap JSX
        assert "Important" in result
        assert "<Callout>" not in result

        # Should remove boilerplate links
        assert "Edit this page" not in result

        # Should preserve frontmatter
        assert "title: Test" in result

    def test_apply_transforms_balanced(self):
        """Test balanced profile applies moderate compression."""
        # Create content with large code block
        lines = ["const line" + str(i) + ' = "value";' for i in range(30)]
        content = f"# Test\n\n```javascript\n{chr(10).join(lines)}\n```"

        result = apply_transforms(content, profile="balanced", source_path="test.md")

        # Should compress large blocks
        if len(lines) > 25:
            assert "lines omitted" in result

    def test_apply_transforms_compact(self):
        """Test compact profile applies aggressive compression."""
        # Create content with moderately large code block
        lines = ["const line" + str(i) + ' = "value";' for i in range(20)]
        content = f"# Test\n\n```javascript\n{chr(10).join(lines)}\n```"

        result = apply_transforms(content, profile="compact", source_path="test.md")

        # Should compress even smaller blocks aggressively
        if len(lines) > 15:
            assert "lines omitted" in result
