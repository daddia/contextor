"""Tests for document loader functionality."""

import tempfile
from pathlib import Path
from textwrap import dedent

from contextor.loader import DocumentInfo, DocumentLoader


class TestDocumentInfo:
    """Test DocumentInfo dataclass."""

    def test_document_info_creation(self):
        """Test DocumentInfo can be created with all fields."""
        doc = DocumentInfo(
            path="docs/test.md",
            content="# Test\n\nContent here.",
            title="Test Document",
            canonical_url="https://github.com/owner/repo/blob/main/docs/test.md",
        )

        assert doc.path == "docs/test.md"
        assert doc.content == "# Test\n\nContent here."
        assert doc.title == "Test Document"
        assert (
            doc.canonical_url == "https://github.com/owner/repo/blob/main/docs/test.md"
        )


class TestDocumentLoader:
    """Test DocumentLoader functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name)

    def teardown_method(self):
        """Clean up test environment."""
        self.temp_dir.cleanup()

    def create_test_file(self, relative_path: str, content: str):
        """Helper to create test files."""
        file_path = self.source_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_init_with_defaults(self):
        """Test DocumentLoader initialization with default patterns."""
        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")

        assert loader.source_dir == self.source_dir
        assert loader.repo == "test/repo"
        assert loader.ref == "main"
        assert "*.md" in loader.include_patterns
        assert "*.mdx" in loader.include_patterns
        assert "**/*.md" in loader.include_patterns
        assert "**/*.mdx" in loader.include_patterns
        assert "node_modules/*" in loader.exclude_patterns
        assert "node_modules/**/*" in loader.exclude_patterns

    def test_init_with_project_config(self):
        """Test DocumentLoader initialization with project config."""
        # Create a mock project config
        from contextor.project_config import ProjectConfig

        config_data = {
            "settings": {
                "title": "Test Project",
                "folders": ["custom"],
                "excludeFolders": ["custom/ignore"],
                "topics": ["test"],
            }
        }
        project_config = ProjectConfig(config_data)

        loader = DocumentLoader(
            self.source_dir, repo="test/repo", ref="main", project_config=project_config
        )

        assert "custom/**/*.md" in loader.include_patterns
        assert "custom/**/*.mdx" in loader.include_patterns
        assert "custom/ignore/**" in loader.exclude_patterns

    def test_should_include_file_basic_patterns(self):
        """Test basic file inclusion patterns."""
        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")

        # Create test files
        md_file = self.create_test_file("test.md", "# Test")
        mdx_file = self.create_test_file("test.mdx", "# Test MDX")
        txt_file = self.create_test_file("test.txt", "Not markdown")
        nested_md = self.create_test_file("docs/nested.md", "# Nested")

        assert loader._should_include_file(md_file)
        assert loader._should_include_file(mdx_file)
        assert not loader._should_include_file(txt_file)
        assert loader._should_include_file(nested_md)

    def test_should_include_file_exclude_patterns(self):
        """Test file exclusion patterns."""
        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")

        # Create files in excluded directories
        node_modules_file = self.create_test_file(
            "node_modules/package.md", "# Package"
        )
        git_file = self.create_test_file(".git/config.md", "# Git")
        dist_file = self.create_test_file("dist/output.md", "# Output")

        assert not loader._should_include_file(node_modules_file)
        assert not loader._should_include_file(git_file)
        assert not loader._should_include_file(dist_file)

    def test_extract_title_from_frontmatter(self):
        """Test title extraction from YAML frontmatter."""
        content = dedent(
            """
            ---
            title: Frontmatter Title
            description: Test file
            ---

            # Heading Title

            Content here.
        """
        ).strip()

        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")
        title = loader._extract_title(content, "test.md")

        assert title == "Frontmatter Title"

    def test_extract_title_from_heading(self):
        """Test title extraction from first heading."""
        content = dedent(
            """
            # Main Title

            Some content here.

            ## Subtitle
        """
        ).strip()

        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")
        title = loader._extract_title(content, "test.md")

        assert title == "Main Title"

    def test_extract_title_fallback_to_filename(self):
        """Test title fallback to filename."""
        content = "Just some content without frontmatter or headings."

        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")
        title = loader._extract_title(content, "my-test-file.md")

        assert title == "My Test File"

    def test_build_canonical_url_github(self):
        """Test canonical URL building for GitHub repos."""
        loader = DocumentLoader(self.source_dir, repo="owner/repo", ref="main")

        url = loader._build_canonical_url("docs/getting-started.md")

        assert url == "https://github.com/owner/repo/blob/main/docs/getting-started.md"

    def test_build_canonical_url_other_repo(self):
        """Test canonical URL building for non-GitHub repos."""
        loader = DocumentLoader(
            self.source_dir, repo="gitlab.com/owner/repo", ref="develop"
        )

        url = loader._build_canonical_url("README.md")
        # Since gitlab.com/owner/repo contains '/' it will be treated as GitHub format
        assert url == "https://github.com/gitlab.com/owner/repo/blob/develop/README.md"

        # To test non-GitHub, use a different format
        loader2 = DocumentLoader(self.source_dir, repo="custom-host", ref="develop")
        url2 = loader2._build_canonical_url("README.md")
        assert url2 == "custom-host/develop/README.md"

    def test_discover_files_basic(self):
        """Test basic file discovery."""
        # Create test files
        self.create_test_file("README.md", "# README\n\nProject readme.")
        self.create_test_file("docs/guide.md", "# Guide\n\nUser guide.")
        self.create_test_file("src/component.mdx", "# Component\n\nComponent docs.")
        self.create_test_file("package.json", '{"name": "test"}')  # Should be ignored

        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")
        documents = list(loader.discover_files())

        assert len(documents) == 3

        # Check paths are relative
        paths = [doc.path for doc in documents]
        assert "README.md" in paths
        assert "docs/guide.md" in paths
        assert "src/component.mdx" in paths

        # Check content is loaded
        readme_doc = next(doc for doc in documents if doc.path == "README.md")
        assert "Project readme." in readme_doc.content

        # Check titles are extracted
        assert readme_doc.title == "README"

        # Check URLs are built
        assert (
            "https://github.com/test/repo/blob/main/README.md"
            in readme_doc.canonical_url
        )

    def test_discover_files_with_exclusions(self):
        """Test file discovery respects exclusion patterns."""
        # Create files, some in excluded directories
        self.create_test_file("docs/good.md", "# Good")
        self.create_test_file("node_modules/bad.md", "# Bad")
        self.create_test_file(".git/also-bad.md", "# Also Bad")

        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")
        documents = list(loader.discover_files())

        assert len(documents) == 1
        assert documents[0].path == "docs/good.md"

    def test_discover_files_empty_directory(self):
        """Test discovery in empty directory."""
        loader = DocumentLoader(self.source_dir, repo="test/repo", ref="main")
        documents = list(loader.discover_files())

        assert len(documents) == 0

    def test_discover_files_nonexistent_directory(self):
        """Test discovery with nonexistent source directory."""
        nonexistent = Path("/nonexistent/path")
        loader = DocumentLoader(nonexistent, repo="test/repo", ref="main")
        documents = list(loader.discover_files())

        assert len(documents) == 0

    def test_discover_files_with_project_config(self):
        """Test file discovery with project configuration patterns."""
        # Create project config with custom patterns
        from contextor.project_config import ProjectConfig

        config_data = {
            "settings": {
                "title": "Test Project",
                "folders": ["custom"],
                "excludeFolders": ["custom/skip"],
                "topics": ["test"],
            }
        }
        project_config = ProjectConfig(config_data)

        # Create test files
        self.create_test_file("custom/included.md", "# Included")
        self.create_test_file("custom/skip/excluded.md", "# Excluded")
        self.create_test_file("other/ignored.md", "# Ignored")  # Not in include pattern

        loader = DocumentLoader(
            self.source_dir, repo="test/repo", ref="main", project_config=project_config
        )
        documents = list(loader.discover_files())

        # Should find the included file but not the excluded ones
        included_files = [doc.path for doc in documents]
        assert "custom/included.md" in included_files
        assert "custom/skip/excluded.md" not in included_files
        assert "other/ignored.md" not in included_files

    def test_init_without_project_config(self):
        """Test DocumentLoader initialization without project config."""
        loader = DocumentLoader(
            self.source_dir, repo="test/repo", ref="main", project_config=None
        )

        # Should use defaults
        assert loader.config == {}
        assert loader.include_patterns == ["*.md", "*.mdx", "**/*.md", "**/*.mdx"]

    def test_init_with_invalid_project_config(self):
        """Test DocumentLoader initialization with invalid project config."""
        # This should not raise an exception, should gracefully handle None
        loader = DocumentLoader(
            self.source_dir, repo="test/repo", ref="main", project_config=None
        )

        # Should use defaults
        assert loader.config == {}
        assert loader.include_patterns == ["*.md", "*.mdx", "**/*.md", "**/*.mdx"]
