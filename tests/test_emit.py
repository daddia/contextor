"""Tests for MDC emission functionality."""

import json
import tempfile
from pathlib import Path

import frontmatter

from contextor.emit import MDCEmitter
from contextor.utils import content_hash


class TestMDCEmitter:
    """Test MDC emission functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_init_creates_output_directory(self):
        """Test that emitter creates output directory."""
        output_path = self.output_dir / "new_subdir"
        emitter = MDCEmitter(output_path)

        assert emitter.output_dir == output_path
        assert output_path.exists()
        assert emitter.index_path == output_path / "index.jsonl"

    def test_emit_mdc_basic(self):
        """Test basic MDC file emission."""
        emitter = MDCEmitter(self.output_dir)

        content = "# Test Document\n\nThis is test content."
        metadata = {
            "repo": "test/repo",
            "ref": "main",
            "path": "docs/test.md",
            "url": "https://github.com/test/repo/blob/main/docs/test.md",
            "title": "Test Document",
            "topics": ["testing", "docs"],
        }

        was_written = emitter.emit_mdc(content, metadata)

        assert was_written

        # Check file was created
        expected_slug = "repo__docs__test"
        mdc_file = self.output_dir / f"{expected_slug}.mdc"
        assert mdc_file.exists()

        # Check index was updated
        assert emitter.index_path.exists()

    def test_emit_mdc_frontmatter_structure(self):
        """Test that emitted MDC has correct frontmatter structure."""
        emitter = MDCEmitter(self.output_dir)

        content = "# Test\n\nContent here."
        metadata = {
            "repo": "owner/project",
            "ref": "v1.0.0",
            "path": "guide/intro.md",
            "url": "https://github.com/owner/project/blob/v1.0.0/guide/intro.md",
            "title": "Introduction",
            "topics": ["guide", "intro"],
        }

        emitter.emit_mdc(content, metadata)

        # Read and parse the generated file
        slug = "project__guide__intro"
        mdc_file = self.output_dir / f"{slug}.mdc"

        with open(mdc_file, encoding="utf-8") as f:
            post = frontmatter.load(f)

        # Check frontmatter fields
        assert post.metadata["schema"] == "mdc/1.0"
        assert post.metadata["source"]["repo"] == "owner/project"
        assert post.metadata["source"]["ref"] == "v1.0.0"
        assert post.metadata["source"]["path"] == "guide/intro.md"
        assert (
            post.metadata["source"]["url"]
            == "https://github.com/owner/project/blob/v1.0.0/guide/intro.md"
        )
        assert post.metadata["title"] == "Introduction"
        assert post.metadata["topics"] == ["guide", "intro"]
        assert post.metadata["slug"] == slug
        assert post.metadata["license"] == "See source repository"
        assert "content_hash" in post.metadata
        assert "fetched_at" in post.metadata

        # Check content
        assert post.content.strip() == content

    def test_emit_mdc_content_hash(self):
        """Test that content hash is calculated correctly."""
        emitter = MDCEmitter(self.output_dir)

        content = "# Test\n\nContent for hashing."
        expected_hash = content_hash(content)

        metadata = {
            "repo": "test/repo",
            "ref": "main",
            "path": "test.md",
            "url": "https://github.com/test/repo/blob/main/test.md",
            "title": "Test",
            "topics": [],
        }

        emitter.emit_mdc(content, metadata)

        # Read and check hash
        slug = "repo__test"
        mdc_file = self.output_dir / f"{slug}.mdc"

        with open(mdc_file, encoding="utf-8") as f:
            post = frontmatter.load(f)

        assert post.metadata["content_hash"] == expected_hash

    def test_emit_mdc_slug_generation(self):
        """Test slug generation from repo and path."""
        emitter = MDCEmitter(self.output_dir)

        test_cases = [
            ("simple/repo", "file.md", "repo__file"),
            (
                "owner/complex-name",
                "docs/api/reference.md",
                "complex-name__docs__api__reference",
            ),
            ("org/project", "README.md", "project__README"),
        ]

        for repo, path, expected_slug in test_cases:
            content = f"# Content for {path}"
            metadata = {
                "repo": repo,
                "ref": "main",
                "path": path,
                "url": f"https://github.com/{repo}/blob/main/{path}",
                "title": "Test",
                "topics": [],
            }

            emitter.emit_mdc(content, metadata)

            mdc_file = self.output_dir / f"{expected_slug}.mdc"
            assert mdc_file.exists()

    def test_emit_mdc_idempotent_same_content(self):
        """Test that identical content is not rewritten."""
        emitter = MDCEmitter(self.output_dir)

        content = "# Same Content\n\nThis content is identical."
        metadata = {
            "repo": "test/repo",
            "ref": "main",
            "path": "same.md",
            "url": "https://github.com/test/repo/blob/main/same.md",
            "title": "Same Content",
            "topics": [],
        }

        # First emission
        was_written_1 = emitter.emit_mdc(content, metadata)
        assert was_written_1

        # Second emission with same content
        was_written_2 = emitter.emit_mdc(content, metadata)
        assert not was_written_2  # Should be skipped

    def test_emit_mdc_not_idempotent_different_content(self):
        """Test that different content causes rewrite."""
        emitter = MDCEmitter(self.output_dir)

        metadata = {
            "repo": "test/repo",
            "ref": "main",
            "path": "changing.md",
            "url": "https://github.com/test/repo/blob/main/changing.md",
            "title": "Changing Content",
            "topics": [],
        }

        # First emission
        content_1 = "# Version 1\n\nOriginal content."
        was_written_1 = emitter.emit_mdc(content_1, metadata)
        assert was_written_1

        # Second emission with different content
        content_2 = "# Version 2\n\nModified content."
        was_written_2 = emitter.emit_mdc(content_2, metadata)
        assert was_written_2  # Should be rewritten

    def test_index_jsonl_creation(self):
        """Test that index.jsonl is created and updated."""
        emitter = MDCEmitter(self.output_dir)

        # Emit first file
        emitter.emit_mdc(
            "# First",
            {
                "repo": "test/repo",
                "ref": "main",
                "path": "first.md",
                "url": "https://github.com/test/repo/blob/main/first.md",
                "title": "First",
                "topics": ["first"],
            },
        )

        # Emit second file
        emitter.emit_mdc(
            "# Second",
            {
                "repo": "test/repo",
                "ref": "main",
                "path": "second.md",
                "url": "https://github.com/test/repo/blob/main/second.md",
                "title": "Second",
                "topics": ["second"],
            },
        )

        # Read and parse index
        with open(emitter.index_path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        assert len(lines) == 2

        # Parse JSON entries
        entries = [json.loads(line) for line in lines]

        # Check first entry
        first_entry = next(e for e in entries if e["slug"] == "repo__first")
        assert first_entry["title"] == "First"
        assert first_entry["path"] == "first.md"
        assert first_entry["repo"] == "test/repo"
        assert first_entry["topics"] == ["first"]

        # Check second entry
        second_entry = next(e for e in entries if e["slug"] == "repo__second")
        assert second_entry["title"] == "Second"
        assert second_entry["path"] == "second.md"
        assert second_entry["topics"] == ["second"]

    def test_index_jsonl_update_existing_entry(self):
        """Test that index.jsonl updates existing entries."""
        emitter = MDCEmitter(self.output_dir)

        metadata = {
            "repo": "test/repo",
            "ref": "main",
            "path": "updating.md",
            "url": "https://github.com/test/repo/blob/main/updating.md",
            "title": "Original Title",
            "topics": ["original"],
        }

        # First emission
        emitter.emit_mdc("# Original", metadata)

        # Update metadata and emit again
        metadata["title"] = "Updated Title"
        metadata["topics"] = ["updated"]
        emitter.emit_mdc("# Updated", metadata)

        # Read index
        with open(emitter.index_path, encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        # Should only have one entry (updated)
        assert len(lines) == 1

        entry = json.loads(lines[0])
        assert entry["title"] == "Updated Title"
        assert entry["topics"] == ["updated"]
        assert entry["slug"] == "repo__updating"

    def test_should_skip_write_missing_file(self):
        """Test skip logic when file doesn't exist."""
        emitter = MDCEmitter(self.output_dir)
        nonexistent = self.output_dir / "nonexistent.mdc"

        should_skip = emitter._should_skip_write(nonexistent, "any_hash")
        assert not should_skip

    def test_should_skip_write_same_hash(self):
        """Test skip logic when hash matches."""
        emitter = MDCEmitter(self.output_dir)

        # Create a file first
        content = "# Test content"
        hash_value = content_hash(content)

        metadata = {
            "repo": "test/repo",
            "ref": "main",
            "path": "test.md",
            "url": "https://github.com/test/repo/blob/main/test.md",
            "title": "Test",
            "topics": [],
        }

        emitter.emit_mdc(content, metadata)

        # Test skip logic
        mdc_file = self.output_dir / "repo__test.mdc"
        should_skip = emitter._should_skip_write(mdc_file, hash_value)
        assert should_skip

    def test_should_skip_write_different_hash(self):
        """Test skip logic when hash differs."""
        emitter = MDCEmitter(self.output_dir)

        # Create a file first
        original_content = "# Original content"
        emitter.emit_mdc(
            original_content,
            {
                "repo": "test/repo",
                "ref": "main",
                "path": "test.md",
                "url": "https://github.com/test/repo/blob/main/test.md",
                "title": "Test",
                "topics": [],
            },
        )

        # Test with different content hash
        different_content = "# Different content"
        different_hash = content_hash(different_content)

        mdc_file = self.output_dir / "repo__test.mdc"
        should_skip = emitter._should_skip_write(mdc_file, different_hash)
        assert not should_skip

    def test_dict_to_yaml_simple(self):
        """Test YAML generation from dictionary."""
        emitter = MDCEmitter(self.output_dir)

        data = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": ["item1", "item2"],
            "nested": {"key": "nested_value"},
        }

        yaml_lines = emitter._dict_to_yaml(data)
        yaml_content = "\n".join(yaml_lines)

        # Check that all keys are present
        assert 'string: "value"' in yaml_content
        assert "number: 42" in yaml_content
        assert "boolean: True" in yaml_content
        assert "nested:" in yaml_content
        assert 'key: "nested_value"' in yaml_content
        assert '- "item1"' in yaml_content
        assert '- "item2"' in yaml_content
