"""Tests for utility functions."""

import tempfile
from pathlib import Path

from contextor.utils import content_hash, ensure_directory, path_to_slug, slugify


class TestSlugify:
    """Test slugify function."""

    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test String") == "test-string"

    def test_slugify_special_characters(self):
        """Test slugification with special characters."""
        assert slugify("Hello, World!") == "hello-world"
        assert slugify("Test & Example") == "test-example"
        assert slugify("File/Path\\Name") == "file-path-name"

    def test_slugify_multiple_spaces(self):
        """Test slugification with multiple spaces."""
        assert slugify("Multiple   Spaces") == "multiple-spaces"
        assert slugify("  Leading and trailing  ") == "leading-and-trailing"

    def test_slugify_numbers_and_letters(self):
        """Test slugification preserves numbers and letters."""
        assert slugify("API v2.1") == "api-v2.1"
        assert slugify("Python 3.11") == "python-3.11"

    def test_slugify_empty_string(self):
        """Test slugification of empty string."""
        assert slugify("") == ""
        assert slugify("   ") == ""

    def test_slugify_already_slug(self):
        """Test slugification of already-slug strings."""
        assert slugify("already-a-slug") == "already-a-slug"
        assert slugify("kebab-case-string") == "kebab-case-string"


class TestContentHash:
    """Test content_hash function."""

    def test_content_hash_deterministic(self):
        """Test that content hash is deterministic."""
        content = "This is test content."
        hash1 = content_hash(content)
        hash2 = content_hash(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_content_hash_different_content(self):
        """Test that different content produces different hashes."""
        content1 = "First content"
        content2 = "Second content"

        hash1 = content_hash(content1)
        hash2 = content_hash(content2)

        assert hash1 != hash2

    def test_content_hash_empty_string(self):
        """Test content hash of empty string."""
        empty_hash = content_hash("")
        assert len(empty_hash) == 64
        assert (
            empty_hash
            == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )  # Known SHA-256 of empty string

    def test_content_hash_unicode(self):
        """Test content hash with unicode characters."""
        unicode_content = "Hello 世界! 🌍"
        hash_result = content_hash(unicode_content)

        assert len(hash_result) == 64
        # Should be deterministic
        assert hash_result == content_hash(unicode_content)

    def test_content_hash_multiline(self):
        """Test content hash with multiline content."""
        multiline = """# Title

This is a multiline
content string with
various lines."""

        hash_result = content_hash(multiline)
        assert len(hash_result) == 64


class TestPathToSlug:
    """Test path_to_slug function."""

    def test_path_to_slug_basic(self):
        """Test basic path to slug conversion."""
        assert path_to_slug("file.md", "repo") == "repo__file"
        assert path_to_slug("docs/guide.md", "project") == "project__docs__guide"

    def test_path_to_slug_removes_extension(self):
        """Test that file extensions are removed."""
        assert path_to_slug("readme.md", "repo") == "repo__readme"
        assert path_to_slug("component.mdx", "repo") == "repo__component"
        assert (
            path_to_slug("config.yaml", "repo") == "repo__config__yaml"
        )  # Only .md/.mdx removed

    def test_path_to_slug_nested_paths(self):
        """Test nested path conversion."""
        assert (
            path_to_slug("docs/api/reference.md", "project")
            == "project__docs__api__reference"
        )
        assert (
            path_to_slug("src/components/Button.mdx", "ui-lib")
            == "ui-lib__src__components__Button"
        )

    def test_path_to_slug_source_slugification(self):
        """Test that source name is slugified."""
        assert path_to_slug("file.md", "My Project") == "my-project__file"
        assert path_to_slug("file.md", "org/repo-name") == "org-repo-name__file"

    def test_path_to_slug_path_object(self):
        """Test with Path objects."""
        path_obj = Path("docs/getting-started.md")
        assert path_to_slug(path_obj, "repo") == "repo__docs__getting-started"

    def test_path_to_slug_special_characters(self):
        """Test path with special characters."""
        assert path_to_slug("api-v2/users.md", "api-docs") == "api-docs__api-v2__users"
        assert (
            path_to_slug("guides/how-to-use.md", "project")
            == "project__guides__how-to-use"
        )

    def test_path_to_slug_root_file(self):
        """Test root-level files."""
        assert path_to_slug("README.md", "repo") == "repo__README"
        assert path_to_slug("CHANGELOG.md", "project") == "project__CHANGELOG"


class TestEnsureDirectory:
    """Test ensure_directory function."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def test_ensure_directory_new_directory(self):
        """Test creating a new directory."""
        new_dir = self.base_path / "new_directory"
        assert not new_dir.exists()

        result = ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_ensure_directory_existing_directory(self):
        """Test with existing directory."""
        existing_dir = self.base_path / "existing"
        existing_dir.mkdir()

        result = ensure_directory(existing_dir)

        assert existing_dir.exists()
        assert existing_dir.is_dir()
        assert result == existing_dir

    def test_ensure_directory_nested_path(self):
        """Test creating nested directories."""
        nested_path = self.base_path / "level1" / "level2" / "level3"
        assert not nested_path.exists()

        result = ensure_directory(nested_path)

        assert nested_path.exists()
        assert nested_path.is_dir()
        assert result == nested_path

        # Check parent directories were also created
        assert (self.base_path / "level1").exists()
        assert (self.base_path / "level1" / "level2").exists()

    def test_ensure_directory_string_path(self):
        """Test with string path."""
        str_path = str(self.base_path / "string_path")

        result = ensure_directory(str_path)

        assert Path(str_path).exists()
        assert Path(str_path).is_dir()
        assert result == Path(str_path)

    def test_ensure_directory_absolute_path(self):
        """Test with absolute path."""
        abs_path = self.base_path / "absolute_test"

        result = ensure_directory(abs_path)

        assert abs_path.exists()
        assert abs_path.is_dir()
        assert result.is_absolute()

    def test_ensure_directory_permissions(self):
        """Test that created directory has correct permissions."""
        new_dir = self.base_path / "permissions_test"

        result = ensure_directory(new_dir)

        assert result.exists()
        assert result.is_dir()
        # Directory should be readable and writable
        assert result.stat().st_mode & 0o700  # At least owner read/write/execute
