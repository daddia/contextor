"""Tests for Advanced Content Intelligence functionality."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import frontmatter

from contextor.intelligence import (
    IntelligenceAnalyzer,
    TopicExtractor,
    QualityScorer,
    SimilarityAnalyzer,
    CrossLinker,
)


@pytest.fixture
def temp_source_dir():
    """Create a temporary directory with sample .mdc files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir)
        
        # Create sample .mdc files
        sample_docs = [
            {
                "slug": "nextjs__getting-started",
                "title": "Getting Started with Next.js",
                "content": """# Getting Started with Next.js

Next.js is a React framework that enables functionality such as server-side rendering and generating static websites.

## Installation

To install Next.js, run:

```bash
npm install next react react-dom
```

## Creating Pages

Pages in Next.js are React components exported from files in the `pages` directory.

### Example

Here's a simple page:

```jsx
export default function Home() {
  return <h1>Welcome to Next.js!</h1>
}
```

## Routing

Next.js has a file-system based router built on the concept of pages.
""",
                "metadata": {
                    "schema": "mdc/1.0",
                    "source": {
                        "repo": "vercel/next.js",
                        "ref": "main",
                        "path": "docs/getting-started.md",
                        "url": "https://github.com/vercel/next.js/blob/main/docs/getting-started.md"
                    },
                    "topics": ["framework", "nextjs"],
                    "content_hash": "abc123",
                    "fetched_at": "2025-01-27T10:30:00Z",
                    "slug": "nextjs__getting-started",
                    "license": "See source repository"
                }
            },
            {
                "slug": "nextjs__routing",
                "title": "Routing in Next.js",
                "content": """# Routing in Next.js

Next.js has a powerful routing system based on the file system.

## File-based Routing

Every file in the `pages` directory becomes a route automatically.

## Dynamic Routes

You can create dynamic routes using brackets in the filename.

### Example

Create a file called `pages/posts/[id].js`:

```jsx
import { useRouter } from 'next/router'

export default function Post() {
  const router = useRouter()
  const { id } = router.query
  
  return <p>Post: {id}</p>
}
```

## API Routes

API routes provide a solution to build your API with Next.js.
""",
                "metadata": {
                    "schema": "mdc/1.0",
                    "source": {
                        "repo": "vercel/next.js",
                        "ref": "main", 
                        "path": "docs/routing.md",
                        "url": "https://github.com/vercel/next.js/blob/main/docs/routing.md"
                    },
                    "topics": ["framework", "nextjs", "routing"],
                    "content_hash": "def456",
                    "fetched_at": "2025-01-27T10:30:00Z",
                    "slug": "nextjs__routing",
                    "license": "See source repository"
                }
            },
            {
                "slug": "react__hooks",
                "title": "React Hooks",
                "content": """# React Hooks

Hooks are functions that let you use state and other React features in functional components.

## useState

The `useState` hook lets you add state to functional components.

```jsx
import { useState } from 'react'

function Counter() {
  const [count, setCount] = useState(0)
  
  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  )
}
```

## useEffect

The `useEffect` hook lets you perform side effects in functional components.
""",
                "metadata": {
                    "schema": "mdc/1.0",
                    "source": {
                        "repo": "facebook/react",
                        "ref": "main",
                        "path": "docs/hooks.md", 
                        "url": "https://github.com/facebook/react/blob/main/docs/hooks.md"
                    },
                    "topics": ["react", "hooks"],
                    "content_hash": "ghi789",
                    "fetched_at": "2025-01-27T10:30:00Z",
                    "slug": "react__hooks",
                    "license": "See source repository"
                }
            }
        ]
        
        # Write sample .mdc files
        for doc in sample_docs:
            doc_path = source_dir / f"{doc['slug']}.mdc"
            post = frontmatter.Post(doc["content"], **doc["metadata"])
            
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(frontmatter.dumps(post))
                
        yield source_dir


class TestTopicExtractor:
    """Test topic extraction functionality."""
    
    def test_extract_topics_from_content(self):
        """Test topic extraction from document content."""
        extractor = TopicExtractor()
        
        content = """# React Components

React components are the building blocks of React applications.

## Functional Components

Functional components are JavaScript functions that return JSX.

## Class Components  

Class components extend React.Component and have a render method.
"""
        metadata = {
            "title": "React Components",
            "topics": ["react"],
            "source": {"path": "docs/components.md"}
        }
        
        topics = extractor.extract_topics(content, metadata)
        
        assert "react" in topics
        assert "components" in topics
        assert len(topics) <= extractor.max_topics
        
    def test_extract_from_path(self):
        """Test topic extraction from file paths."""
        extractor = TopicExtractor()
        
        topics = extractor._extract_from_path("docs/api/authentication.md")
        
        assert "docs" in topics
        assert "api" in topics
        assert "authentication" in topics
        
    def test_extract_from_headings(self):
        """Test topic extraction from markdown headings."""
        extractor = TopicExtractor()
        
        content = """# Getting Started Guide

## Installation Steps

### Prerequisites

## Configuration Options
"""
        
        topics = extractor._extract_from_headings(content)
        
        assert "getting" in topics
        assert "started" in topics
        assert "installation" in topics
        assert "configuration" in topics


class TestQualityScorer:
    """Test quality scoring functionality."""
    
    def test_score_quality_complete_document(self):
        """Test quality scoring for a complete document."""
        scorer = QualityScorer()
        
        content = """# Complete Guide

This is a comprehensive guide with multiple sections.

## Section One

Content with good structure and explanations.

## Section Two

More detailed content with examples:

```python
def example():
    return "Hello World"
```

## Links and References

See [official docs](https://example.com) for more information.

The document has good length and structure.
"""
        
        metadata = {
            "title": "Complete Guide",
            "fetched_at": "2025-01-27T10:30:00Z"
        }
        
        quality = scorer.score_quality(content, metadata)
        
        assert "completeness" in quality
        assert "freshness" in quality
        assert "clarity" in quality
        assert "overall" in quality
        
        assert 0 <= quality["completeness"] <= 1
        assert 0 <= quality["freshness"] <= 1
        assert 0 <= quality["clarity"] <= 1
        assert 0 <= quality["overall"] <= 1
        
    def test_score_completeness(self):
        """Test completeness scoring."""
        scorer = QualityScorer()
        
        # Complete document
        complete_content = """# Title

## Section 1
Good content with examples.

```code
example
```

[Link](http://example.com)

## Section 2
More content here.
"""
        complete_metadata = {"title": "Test Document"}
        
        completeness = scorer._score_completeness(complete_content, complete_metadata)
        assert completeness > 0.5
        
        # Incomplete document
        incomplete_content = "Short content"
        incomplete_metadata = {}
        
        incompleteness = scorer._score_completeness(incomplete_content, incomplete_metadata)
        assert incompleteness < completeness
        
    def test_score_freshness(self):
        """Test freshness scoring."""
        scorer = QualityScorer()
        
        # Recent document
        recent_metadata = {"fetched_at": "2025-01-27T10:30:00Z"}
        recent_freshness = scorer._score_freshness(recent_metadata)
        assert recent_freshness > 0.8
        
        # Old document
        old_metadata = {"fetched_at": "2020-01-01T10:30:00Z"}
        old_freshness = scorer._score_freshness(old_metadata)
        assert old_freshness < recent_freshness


class TestSimilarityAnalyzer:
    """Test similarity analysis functionality."""
    
    def test_generate_fingerprint(self):
        """Test content fingerprint generation."""
        analyzer = SimilarityAnalyzer()
        
        content1 = "This is a test document with some content."
        content2 = "This is a test document with some content."
        content3 = "This is completely different content."
        
        fingerprint1 = analyzer.generate_fingerprint(content1)
        fingerprint2 = analyzer.generate_fingerprint(content2)
        fingerprint3 = analyzer.generate_fingerprint(content3)
        
        assert fingerprint1 == fingerprint2  # Same content
        assert fingerprint1 != fingerprint3  # Different content
        assert len(fingerprint1) == 16  # Expected length
        
    def test_generate_content_vector(self):
        """Test content vector generation."""
        analyzer = SimilarityAnalyzer()
        
        content = "This is a test document with some repeated words. Test document example."
        vector = analyzer._generate_content_vector(content)
        
        assert "test" in vector
        assert "document" in vector
        assert vector["test"] >= 1
        assert vector["document"] >= 1
        
    def test_calculate_similarity(self):
        """Test similarity calculation between vectors."""
        analyzer = SimilarityAnalyzer()
        
        from collections import Counter
        
        vector1 = Counter({"react": 3, "components": 2, "hooks": 1})
        vector2 = Counter({"react": 2, "components": 3, "state": 1})
        vector3 = Counter({"python": 3, "django": 2, "models": 1})
        
        # Similar vectors
        similarity1 = analyzer._calculate_similarity(vector1, vector2)
        assert similarity1 > 0.5
        
        # Different vectors
        similarity2 = analyzer._calculate_similarity(vector1, vector3)
        assert similarity2 == 0.0
        
        # Same vector
        similarity3 = analyzer._calculate_similarity(vector1, vector1)
        assert similarity3 == 1.0


class TestCrossLinker:
    """Test cross-linking functionality."""
    
    def test_find_related_documents(self):
        """Test finding related documents."""
        linker = CrossLinker()
        
        # Create sample documents
        doc1 = {
            "slug": "react-hooks",
            "title": "React Hooks",
            "content": "React hooks are functions that let you use state.",
            "metadata": {"topics": ["react", "hooks"]},
            "intelligence": {
                "extracted_topics": ["react", "hooks", "state"],
                "content_fingerprint": "abc123"
            }
        }
        
        doc2 = {
            "slug": "react-components",
            "title": "React Components", 
            "content": "React components are the building blocks.",
            "metadata": {"topics": ["react", "components"]},
            "intelligence": {
                "extracted_topics": ["react", "components"],
                "content_fingerprint": "def456"
            }
        }
        
        doc3 = {
            "slug": "python-basics",
            "title": "Python Basics",
            "content": "Python is a programming language.",
            "metadata": {"topics": ["python"]},
            "intelligence": {
                "extracted_topics": ["python", "programming"],
                "content_fingerprint": "ghi789"
            }
        }
        
        documents = [doc1, doc2, doc3]
        related = linker.find_related_documents(doc1, documents)
        
        # Should find doc2 as related (both about React)
        assert len(related) >= 1
        assert any(r["slug"] == "react-components" for r in related)
        
        # Should not include doc3 (different topic)
        assert not any(r["slug"] == "python-basics" for r in related)
        
    def test_calculate_path_similarity(self):
        """Test path similarity calculation."""
        linker = CrossLinker()
        
        doc1 = {
            "metadata": {
                "source": {"path": "docs/react/hooks.md"}
            }
        }
        
        doc2 = {
            "metadata": {
                "source": {"path": "docs/react/components.md"}
            }
        }
        
        doc3 = {
            "metadata": {
                "source": {"path": "docs/python/basics.md"}
            }
        }
        
        # Same directory
        similarity1 = linker._calculate_path_similarity(doc1, doc2)
        assert similarity1 > 0.5
        
        # Different directories
        similarity2 = linker._calculate_path_similarity(doc1, doc3)
        assert similarity2 < similarity1


class TestIntelligenceAnalyzer:
    """Test the main intelligence analyzer."""
    
    def test_analyzer_initialization(self, temp_source_dir):
        """Test analyzer initialization."""
        analyzer = IntelligenceAnalyzer(temp_source_dir)
        
        assert analyzer.source_dir == temp_source_dir
        assert analyzer.topic_extractor is not None
        assert analyzer.quality_scorer is not None
        assert analyzer.similarity_analyzer is not None
        assert analyzer.cross_linker is not None
        
    def test_filter_files_for_analysis(self, temp_source_dir):
        """Test file filtering for incremental analysis."""
        analyzer = IntelligenceAnalyzer(temp_source_dir)
        
        mdc_files = list(temp_source_dir.rglob("*.mdc"))
        
        # Full analysis - should include all files
        all_files = analyzer._filter_files_for_analysis(mdc_files, incremental=False)
        assert len(all_files) == len(mdc_files)
        
        # Incremental analysis - should include all files first time
        incremental_files = analyzer._filter_files_for_analysis(mdc_files, incremental=True)
        assert len(incremental_files) == len(mdc_files)
        
    def test_analyze_document(self, temp_source_dir):
        """Test single document analysis."""
        config = {
            "topic_extraction": {"max_topics": 5},
            "quality_scoring": {},
            "similarity": {},
        }
        analyzer = IntelligenceAnalyzer(temp_source_dir, config)
        
        mdc_files = list(temp_source_dir.rglob("*.mdc"))
        features = {"topic-extraction", "quality-scoring", "duplicate-detection"}
        
        doc_data = analyzer._analyze_document(mdc_files[0], features)
        
        assert doc_data is not None
        assert "intelligence" in doc_data
        assert "extracted_topics" in doc_data["intelligence"]
        assert "quality_metrics" in doc_data["intelligence"]
        assert "content_fingerprint" in doc_data["intelligence"]
        assert "last_analyzed" in doc_data["intelligence"]
        
    @patch('contextor.intelligence.analyzer.logger')
    def test_analyze_full_workflow(self, mock_logger, temp_source_dir):
        """Test the complete analysis workflow."""
        analyzer = IntelligenceAnalyzer(temp_source_dir)
        
        features = {"topic-extraction", "quality-scoring", "cross-linking"}
        results = analyzer.analyze(features=features, incremental=False)
        
        assert "processed" in results
        assert "updated" in results
        assert "errors" in results
        assert results["processed"] > 0
        
        # Check that intelligence index was created
        intelligence_index = temp_source_dir / "intelligence.jsonl"
        assert intelligence_index.exists()
        
        # Check that .mdc files were updated with intelligence data
        mdc_files = list(temp_source_dir.rglob("*.mdc"))
        with open(mdc_files[0], encoding="utf-8") as f:
            post = frontmatter.load(f)
            assert "intelligence" in post.metadata
            
    def test_load_save_analysis_state(self, temp_source_dir):
        """Test analysis state persistence."""
        analyzer = IntelligenceAnalyzer(temp_source_dir)
        
        mdc_files = list(temp_source_dir.rglob("*.mdc"))
        
        # Save state
        analyzer._save_analysis_state(mdc_files)
        
        # Check state file exists
        state_file = temp_source_dir / ".intelligence-state.json"
        assert state_file.exists()
        
        # Load state
        state = analyzer._load_analysis_state()
        assert len(state) > 0
        
        # Check state contains expected data
        for mdc_path in mdc_files:
            relative_path = str(mdc_path.relative_to(temp_source_dir))
            assert relative_path in state
            assert "content_hash" in state[relative_path]
            assert "last_analyzed" in state[relative_path]


@pytest.mark.integration
class TestIntelligenceIntegration:
    """Integration tests for intelligence functionality."""
    
    def test_cli_integration(self, temp_source_dir):
        """Test CLI integration with intelligence command."""
        from contextor.__main__ import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        # Mock the intelligence module import
        with patch('contextor.__main__.IntelligenceAnalyzer') as mock_analyzer:
            mock_instance = Mock()
            mock_instance.analyze.return_value = {
                "processed": 3,
                "updated": 3,
                "skipped": 0,
                "errors": 0
            }
            mock_analyzer.return_value = mock_instance
            
            result = runner.invoke(cli, [
                'intelligence',
                '--source-dir', str(temp_source_dir),
                '--features', 'topic-extraction,quality-scoring'
            ])
            
            assert result.exit_code == 0
            mock_analyzer.assert_called_once()
            mock_instance.analyze.assert_called_once()
            
    def test_configuration_loading(self, temp_source_dir):
        """Test configuration file loading."""
        config_content = """
topic_extraction:
  max_topics: 8
  min_frequency: 1
  
quality_scoring:
  completeness_weight: 0.5
  freshness_weight: 0.3
  clarity_weight: 0.2
"""
        
        config_file = temp_source_dir / "test_config.yaml"
        with open(config_file, "w") as f:
            f.write(config_content)
            
        from contextor.__main__ import cli
        from click.testing import CliRunner
        
        runner = CliRunner()
        
        with patch('contextor.__main__.IntelligenceAnalyzer') as mock_analyzer:
            mock_instance = Mock()
            mock_instance.analyze.return_value = {"processed": 0, "errors": 0}
            mock_analyzer.return_value = mock_instance
            
            result = runner.invoke(cli, [
                'intelligence',
                '--source-dir', str(temp_source_dir),
                '--config', str(config_file)
            ])
            
            assert result.exit_code == 0
            
            # Check that config was passed to analyzer
            call_args = mock_analyzer.call_args
            config_arg = call_args[0][1]  # Second argument is config
            assert "topic_extraction" in config_arg
            assert config_arg["topic_extraction"]["max_topics"] == 8
