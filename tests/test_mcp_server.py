"""
Contract tests for Contextor MCP Server tools
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from contextor.mcp_server.handlers import SourceDocsHandlers
from contextor.mcp_server.server import create_app


@pytest.fixture
def temp_sourcedocs():
    """Create a temporary sourcedocs directory with test content"""
    with tempfile.TemporaryDirectory() as temp_dir:
        sourcedocs_path = Path(temp_dir) / "sourcedocs"
        sourcedocs_path.mkdir()

        # Create test content structure
        anthropic_dir = sourcedocs_path / "anthropic"
        anthropic_dir.mkdir()

        # Create sample markdown files
        (anthropic_dir / "mcp-connector.md").write_text(
            """
# MCP Connector

Claude's Model Context Protocol (MCP) connector feature enables you to connect to remote MCP servers.

## Key Features

* Direct API integration
* Tool calling support
* OAuth authentication
"""
        )

        (anthropic_dir / "remote-mcp-servers.md").write_text(
            """
# Remote MCP Servers

This document describes how to set up remote MCP servers.

## Configuration

You can configure remote servers using the following format.
"""
        )

        # Create another source
        prompt_eng_dir = sourcedocs_path / "prompt-engineering" / "anthropic"
        prompt_eng_dir.mkdir(parents=True)

        (prompt_eng_dir / "system-prompts.md").write_text(
            """
# System Prompts

System prompts are instructions that guide Claude's behavior.

## Best Practices

1. Be clear and specific
2. Use examples when helpful
3. Set appropriate tone
"""
        )

        yield sourcedocs_path


@pytest.fixture
def handlers(temp_sourcedocs):
    """Create handlers instance with test data"""
    return SourceDocsHandlers(temp_sourcedocs)


@pytest.fixture
def client(temp_sourcedocs):
    """Create FastAPI test client with test data"""
    app = create_app(temp_sourcedocs)
    return TestClient(app)


class TestListSource:
    """Test the list_source tool"""

    @pytest.mark.asyncio
    async def test_list_all_sources(self, handlers):
        """Test listing all sources"""
        result = await handlers.list_source()

        assert result["status"] == "success"
        assert "sources" in result
        assert result["total_sources"] >= 2

        # Check that we have both sources
        source_slugs = [s["slug"] for s in result["sources"]]
        assert "anthropic" in source_slugs
        assert "prompt-engineering" in source_slugs

    @pytest.mark.asyncio
    async def test_list_specific_source(self, handlers):
        """Test listing a specific source"""
        result = await handlers.list_source(source_slug="anthropic")

        assert result["status"] == "success"
        assert result["source"] == "anthropic"
        assert "files" in result
        assert result["total_files"] >= 2

        # Check file names
        file_names = [f["name"] for f in result["files"]]
        assert "mcp-connector.md" in file_names
        assert "remote-mcp-servers.md" in file_names

    @pytest.mark.asyncio
    async def test_list_nonexistent_source(self, handlers):
        """Test listing a nonexistent source"""
        result = await handlers.list_source(source_slug="nonexistent")

        assert result["status"] == "not_found"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_list_with_stats(self, handlers):
        """Test listing with statistics"""
        result = await handlers.list_source(include_stats=True)

        assert result["status"] == "success"

        for source in result["sources"]:
            assert "file_count" in source
            assert "total_size" in source
            assert source["file_count"] > 0
            assert source["total_size"] > 0


class TestGetFile:
    """Test the get_file tool"""

    @pytest.mark.asyncio
    async def test_get_file_by_path(self, handlers):
        """Test getting a file by path"""
        result = await handlers.get_file(path="anthropic/mcp-connector.md")

        assert result["status"] == "success"
        assert result["path"] == "anthropic/mcp-connector.md"
        assert "content" in result
        assert "MCP Connector" in result["content"]
        assert "metadata" in result
        assert result["metadata"]["size"] > 0
        assert "modified" in result["metadata"]

    @pytest.mark.asyncio
    async def test_get_file_by_slug(self, handlers):
        """Test getting a file by slug"""
        result = await handlers.get_file(slug="mcp-connector")

        assert result["status"] == "success"
        assert "content" in result
        assert "MCP Connector" in result["content"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_file(self, handlers):
        """Test getting a nonexistent file"""
        result = await handlers.get_file(path="nonexistent/file.md")

        assert result["status"] == "not_found"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_file_no_path_or_slug(self, handlers):
        """Test getting a file without path or slug"""
        result = await handlers.get_file()

        assert result["status"] == "error"
        assert "error" in result


class TestSearch:
    """Test the search tool"""

    @pytest.mark.asyncio
    async def test_search_basic(self, handlers):
        """Test basic search functionality"""
        results = await handlers.search(query="MCP")

        assert isinstance(results, list)
        assert len(results) > 0

        # Check result structure
        for result in results:
            assert "path" in result
            assert "score" in result
            assert "source" in result
            assert result["score"] > 0

    @pytest.mark.asyncio
    async def test_search_with_source_filter(self, handlers):
        """Test search with source filtering"""
        results = await handlers.search(query="MCP", source_filter="anthropic")

        assert isinstance(results, list)
        assert len(results) > 0

        # All results should be from anthropic source
        for result in results:
            assert result["source"] == "anthropic"

    @pytest.mark.asyncio
    async def test_search_with_limit(self, handlers):
        """Test search with result limit"""
        results = await handlers.search(query="the", limit=1)

        assert isinstance(results, list)
        assert len(results) <= 1

    @pytest.mark.asyncio
    async def test_search_with_content(self, handlers):
        """Test search including content snippets"""
        results = await handlers.search(query="MCP", include_content=True)

        assert len(results) > 0

        for result in results:
            assert "preview" in result
            assert len(result["preview"]) > 0

    @pytest.mark.asyncio
    async def test_search_without_content(self, handlers):
        """Test search without content snippets"""
        results = await handlers.search(query="MCP", include_content=False)

        assert len(results) > 0

        for result in results:
            assert "preview" not in result

    @pytest.mark.asyncio
    async def test_search_no_results(self, handlers):
        """Test search with no matching results"""
        results = await handlers.search(query="nonexistent-term-xyz")

        assert isinstance(results, list)
        assert len(results) == 0


class TestStats:
    """Test the stats tool"""

    @pytest.mark.asyncio
    async def test_stats_basic(self, handlers):
        """Test basic statistics"""
        result = await handlers.stats()

        assert result["status"] == "success"
        assert "total_files" in result
        assert "total_size_bytes" in result
        assert "total_size_mb" in result
        assert "file_types" in result
        assert "source_count" in result
        assert "generated_at" in result

        assert result["total_files"] > 0
        assert result["total_size_bytes"] > 0
        assert result["source_count"] >= 2
        assert ".md" in result["file_types"]

    @pytest.mark.asyncio
    async def test_stats_detailed(self, handlers):
        """Test detailed statistics"""
        result = await handlers.stats(detailed=True)

        assert result["status"] == "success"
        assert "sources" in result
        assert len(result["sources"]) >= 2

        # Check source details
        for source_stats in result["sources"].values():
            assert "files" in source_stats
            assert "size" in source_stats
            assert "types" in source_stats
            assert source_stats["files"] > 0
            assert source_stats["size"] > 0


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_sourcedocs_path(self):
        """Test initialization with invalid sourcedocs path"""
        with pytest.raises(ValueError):
            SourceDocsHandlers(Path("/nonexistent/path"))

    @pytest.mark.asyncio
    async def test_search_invalid_source_filter(self, handlers):
        """Test search with invalid source filter"""
        results = await handlers.search(query="test", source_filter="nonexistent")

        assert isinstance(results, list)
        assert len(results) == 0  # Should return empty list, not error


class TestPreviewExtraction:
    """Test preview snippet extraction"""

    @pytest.mark.asyncio
    async def test_preview_extraction(self, handlers):
        """Test that preview extraction works correctly"""
        results = await handlers.search(query="MCP", include_content=True)

        assert len(results) > 0

        result = results[0]  # Get first result
        assert "preview" in result

        preview = result["preview"]
        assert "MCP" in preview  # Query should be in preview
        assert len(preview) > 10  # Should have reasonable length

        # Preview should not be the entire content
        full_result = await handlers.get_file(path=result["path"])
        assert len(preview) < len(full_result["content"])


class TestTimestampFiltering:
    """Test timestamp-based filtering"""

    @pytest.mark.asyncio
    async def test_since_timestamp_filtering(self, handlers):
        """Test filtering by timestamp"""
        # Get current timestamp
        now = datetime.now().isoformat()

        # Should return empty results since files are older
        result = await handlers.list_source(since=now)

        assert result["status"] == "success"
        # All files should be filtered out since they're older than "now"
        for source in result["sources"]:
            if "file_count" in source:
                assert source["file_count"] == 0

    @pytest.mark.asyncio
    async def test_invalid_timestamp_format(self, handlers):
        """Test handling of invalid timestamp format"""
        # Should not crash with invalid timestamp
        result = await handlers.list_source(since="invalid-timestamp")

        assert result["status"] == "success"
        # Should ignore invalid timestamp and return all results
        assert result["total_sources"] >= 2


class TestAPIEndpoints:
    """Test FastAPI HTTP endpoints"""

    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_list_tools_endpoint(self, client):
        """Test tools listing endpoint"""
        response = client.get("/tools")
        assert response.status_code == 200

        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) > 0

    def test_rest_sources_endpoint(self, client):
        """Test REST sources endpoint"""
        response = client.get("/sources")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "sources" in data
        assert data["total_sources"] >= 2

    def test_rest_specific_source_endpoint(self, client):
        """Test REST specific source endpoint"""
        response = client.get("/sources/anthropic")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["source"] == "anthropic"
        assert "files" in data

    def test_rest_nonexistent_source_endpoint(self, client):
        """Test REST nonexistent source endpoint"""
        response = client.get("/sources/nonexistent")
        assert response.status_code == 404

    def test_rest_get_file_endpoint(self, client):
        """Test REST get file endpoint"""
        response = client.get("/files?path=anthropic/mcp-connector.md")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "content" in data
        assert "MCP Connector" in data["content"]

    def test_rest_get_file_by_slug_endpoint(self, client):
        """Test REST get file by slug endpoint"""
        response = client.get("/files?slug=mcp-connector")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "content" in data

    def test_rest_get_nonexistent_file_endpoint(self, client):
        """Test REST get nonexistent file endpoint"""
        response = client.get("/files?path=nonexistent/file.md")
        assert response.status_code == 404

    def test_rest_search_endpoint(self, client):
        """Test REST search endpoint"""
        response = client.get("/search?query=MCP")
        assert response.status_code == 200

        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_rest_stats_endpoint(self, client):
        """Test REST stats endpoint"""
        response = client.get("/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "total_files" in data
        assert data["total_files"] > 0

    def test_mcp_tool_endpoints(self, client):
        """Test MCP-style tool endpoints"""
        # Test list_source tool
        response = client.post("/tools/list_source", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "sources" in data

        # Test get_file tool
        response = client.post(
            "/tools/get_file", json={"path": "anthropic/mcp-connector.md"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "content" in data

        # Test search tool
        response = client.post("/tools/search", json={"query": "MCP"})
        assert response.status_code == 200

        data = response.json()
        assert "results" in data

        # Test stats tool
        response = client.post("/tools/stats", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
