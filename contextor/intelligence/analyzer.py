"""Main intelligence analyzer orchestrating all analysis components."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import frontmatter
import structlog

from ..utils import content_hash
from .cross_linking import CrossLinker
from .quality_scoring import QualityScorer
from .similarity import SimilarityAnalyzer
from .topic_extraction import TopicExtractor

logger = structlog.get_logger()


class IntelligenceAnalyzer:
    """Orchestrates intelligence analysis across document collections."""

    def __init__(
        self,
        source_dir: Path,
        config: Optional[dict[str, Any]] = None,
    ):
        """Initialize the intelligence analyzer.

        Args:
            source_dir: Directory containing .mdc files to analyze
            config: Configuration dictionary for analysis parameters
        """
        self.source_dir = Path(source_dir)
        self.config = config or {}
        self.state_file = self.source_dir / ".intelligence-state.json"
        self.intelligence_index = self.source_dir / "intelligence.jsonl"

        # Initialize analyzers
        self.topic_extractor = TopicExtractor(self.config.get("topic_extraction", {}))
        self.quality_scorer = QualityScorer(self.config.get("quality_scoring", {}))
        self.similarity_analyzer = SimilarityAnalyzer(self.config.get("similarity", {}))
        self.cross_linker = CrossLinker(self.config.get("cross_linking", {}))

        # Load previous analysis state
        self.previous_state = self._load_analysis_state()

    def analyze(
        self,
        features: Optional[set[str]] = None,
        incremental: bool = True,
    ) -> dict[str, Any]:
        """Run intelligence analysis on the document collection.

        Args:
            features: Set of features to enable (topic-extraction, cross-linking,
                     quality-scoring, duplicate-detection)
            incremental: Whether to skip analysis of unchanged documents

        Returns:
            Analysis results and metrics
        """
        if features is None:
            features = {
                "topic-extraction",
                "cross-linking",
                "quality-scoring",
                "duplicate-detection",
            }

        logger.info(
            "Starting intelligence analysis",
            source_dir=str(self.source_dir),
            features=list(features),
            incremental=incremental,
        )

        # Discover .mdc files
        mdc_files = list(self.source_dir.rglob("*.mdc"))
        if not mdc_files:
            logger.warning("No .mdc files found", source_dir=str(self.source_dir))
            return {"error": "No .mdc files found"}

        # Filter files for incremental processing
        files_to_analyze = self._filter_files_for_analysis(mdc_files, incremental)

        logger.info(
            "Files to analyze",
            total_files=len(mdc_files),
            files_to_analyze=len(files_to_analyze),
            incremental=incremental,
        )

        # Phase 1: Individual document analysis
        documents = []
        analysis_results = {
            "processed": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
            "features_enabled": list(features),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        for mdc_path in files_to_analyze:
            try:
                doc_data = self._analyze_document(mdc_path, features)
                if doc_data:
                    documents.append(doc_data)
                    analysis_results["processed"] += 1
                else:
                    analysis_results["skipped"] += 1

            except Exception as e:
                logger.error(
                    "Failed to analyze document", path=str(mdc_path), error=str(e)
                )
                analysis_results["errors"] += 1

        # Phase 2: Cross-document analysis
        if "cross-linking" in features or "duplicate-detection" in features:
            try:
                self._analyze_relationships(documents, features)
                logger.info(
                    "Cross-document analysis complete", document_count=len(documents)
                )
            except Exception as e:
                logger.error("Cross-document analysis failed", error=str(e))
                analysis_results["errors"] += 1

        # Update files with intelligence data
        for doc_data in documents:
            try:
                self._update_mdc_file(doc_data)
                analysis_results["updated"] += 1
            except Exception as e:
                logger.error(
                    "Failed to update document", slug=doc_data["slug"], error=str(e)
                )
                analysis_results["errors"] += 1

        # Update intelligence index
        self._update_intelligence_index(documents)

        # Save analysis state
        self._save_analysis_state(files_to_analyze)

        logger.info(
            "Intelligence analysis complete",
            **{k: v for k, v in analysis_results.items() if k != "features_enabled"},
        )

        return analysis_results

    def _filter_files_for_analysis(
        self, mdc_files: list[Path], incremental: bool
    ) -> list[Path]:
        """Filter files that need analysis based on incremental processing."""
        if not incremental:
            return mdc_files

        files_to_analyze = []

        for mdc_path in mdc_files:
            try:
                with open(mdc_path, encoding="utf-8") as f:
                    post = frontmatter.load(f)

                current_hash = content_hash(post.content)
                relative_path = str(mdc_path.relative_to(self.source_dir))

                # Check if file has changed since last analysis
                previous_hash = self.previous_state.get(relative_path, {}).get(
                    "content_hash"
                )

                if current_hash != previous_hash:
                    files_to_analyze.append(mdc_path)
                else:
                    logger.debug("Skipping unchanged file", path=relative_path)

            except Exception as e:
                logger.warning(
                    "Failed to check file hash", path=str(mdc_path), error=str(e)
                )
                # Include file in analysis if we can't determine if it changed
                files_to_analyze.append(mdc_path)

        return files_to_analyze

    def _analyze_document(
        self, mdc_path: Path, features: set[str]
    ) -> Optional[dict[str, Any]]:
        """Analyze a single document and extract intelligence data."""
        try:
            with open(mdc_path, encoding="utf-8") as f:
                post = frontmatter.load(f)

            doc_data = {
                "path": mdc_path,
                "slug": post.metadata.get("slug", ""),
                "title": post.metadata.get("title", ""),
                "content": post.content,
                "metadata": post.metadata,
                "intelligence": {},
            }

            # Topic extraction
            if "topic-extraction" in features:
                extracted_topics = self.topic_extractor.extract_topics(
                    post.content, post.metadata
                )
                doc_data["intelligence"]["extracted_topics"] = extracted_topics

            # Quality scoring
            if "quality-scoring" in features:
                quality_metrics = self.quality_scorer.score_quality(
                    post.content, post.metadata
                )
                doc_data["intelligence"]["quality_metrics"] = quality_metrics

            # Content fingerprint for similarity analysis
            if "cross-linking" in features or "duplicate-detection" in features:
                fingerprint = self.similarity_analyzer.generate_fingerprint(
                    post.content
                )
                doc_data["intelligence"]["content_fingerprint"] = fingerprint

            doc_data["intelligence"]["last_analyzed"] = (
                datetime.utcnow().isoformat() + "Z"
            )

            return doc_data

        except Exception as e:
            logger.error("Document analysis failed", path=str(mdc_path), error=str(e))
            return None

    def _analyze_relationships(
        self, documents: list[dict[str, Any]], features: set[str]
    ) -> None:
        """Analyze relationships between documents."""
        if "cross-linking" in features:
            # Find related documents
            for doc in documents:
                related = self.cross_linker.find_related_documents(doc, documents)
                doc["intelligence"]["related_documents"] = related

        if "duplicate-detection" in features:
            # Find similar/duplicate documents
            similarities = self.similarity_analyzer.find_similar_documents(documents)

            for doc in documents:
                doc_similarities = similarities.get(doc["slug"], [])
                doc["intelligence"]["similar_documents"] = doc_similarities

    def _update_mdc_file(self, doc_data: dict[str, Any]) -> None:
        """Update .mdc file with intelligence metadata."""
        mdc_path = doc_data["path"]

        # Update metadata with intelligence data
        updated_metadata = doc_data["metadata"].copy()
        updated_metadata["intelligence"] = doc_data["intelligence"]

        # Write updated file
        post = frontmatter.Post(doc_data["content"], **updated_metadata)

        with open(mdc_path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        logger.debug("Updated document with intelligence", path=str(mdc_path))

    def _update_intelligence_index(self, documents: list[dict[str, Any]]) -> None:
        """Update the intelligence index file."""
        try:
            # Load existing index entries
            existing_entries = {}
            if self.intelligence_index.exists():
                with open(self.intelligence_index, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            entry = json.loads(line.strip())
                            existing_entries[entry["slug"]] = entry

            # Update with new intelligence data
            for doc in documents:
                index_entry = {
                    "slug": doc["slug"],
                    "title": doc["title"],
                    "path": str(doc["path"].relative_to(self.source_dir)),
                    "intelligence": doc["intelligence"],
                }
                existing_entries[doc["slug"]] = index_entry

            # Write updated index
            with open(self.intelligence_index, "w", encoding="utf-8") as f:
                for entry in existing_entries.values():
                    f.write(json.dumps(entry) + "\n")

            logger.info("Updated intelligence index", entries=len(existing_entries))

        except Exception as e:
            logger.error("Failed to update intelligence index", error=str(e))

    def _load_analysis_state(self) -> dict[str, Any]:
        """Load previous analysis state from file."""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning("Failed to load analysis state", error=str(e))
            return {}

    def _save_analysis_state(self, analyzed_files: list[Path]) -> None:
        """Save current analysis state to file."""
        try:
            state = {}

            for mdc_path in analyzed_files:
                try:
                    with open(mdc_path, encoding="utf-8") as f:
                        post = frontmatter.load(f)

                    relative_path = str(mdc_path.relative_to(self.source_dir))
                    state[relative_path] = {
                        "content_hash": content_hash(post.content),
                        "last_analyzed": datetime.utcnow().isoformat() + "Z",
                    }
                except Exception as e:
                    logger.warning(
                        "Failed to hash file for state",
                        path=str(mdc_path),
                        error=str(e),
                    )

            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)

            logger.debug("Saved analysis state", files=len(state))

        except Exception as e:
            logger.error("Failed to save analysis state", error=str(e))
