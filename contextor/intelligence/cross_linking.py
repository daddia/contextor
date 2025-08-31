"""Cross-document linking and relationship analysis."""

from typing import Any

import structlog

logger = structlog.get_logger()


class CrossLinker:
    """Identifies relationships and suggests cross-links between documents."""

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize the cross-linker.

        Args:
            config: Configuration for cross-linking
        """
        self.config = config or {}
        self.max_related_documents = self.config.get("max_related_documents", 5)
        self.topic_overlap_threshold = self.config.get("topic_overlap_threshold", 0.3)
        self.relevance_threshold = self.config.get("relevance_threshold", 0.4)

    def find_related_documents(
        self, target_doc: dict[str, Any], all_documents: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find documents related to the target document.

        Args:
            target_doc: Document to find relationships for
            all_documents: Collection of all documents to search

        Returns:
            List of related document information with relevance scores
        """
        related = []
        target_intelligence = target_doc.get("intelligence", {})
        target_topics = set(target_intelligence.get("extracted_topics", []))
        target_metadata_topics = set(target_doc.get("metadata", {}).get("topics", []))

        # Combine all target topics
        all_target_topics = target_topics | target_metadata_topics

        for doc in all_documents:
            # Skip self
            if doc["slug"] == target_doc["slug"]:
                continue

            relevance_score = self._calculate_relevance(
                target_doc, doc, all_target_topics
            )

            if relevance_score >= self.relevance_threshold:
                relationship_type = self._determine_relationship_type(
                    target_doc, doc, relevance_score
                )

                related.append(
                    {
                        "slug": doc["slug"],
                        "title": doc["title"],
                        "relevance": round(relevance_score, 3),
                        "relationship": relationship_type,
                    }
                )

        # Sort by relevance and limit results
        related.sort(key=lambda x: x["relevance"], reverse=True)

        logger.debug(
            "Found related documents",
            target_slug=target_doc["slug"],
            related_count=len(related),
            top_relevance=related[0]["relevance"] if related else 0,
        )

        return related[: self.max_related_documents]

    def _calculate_relevance(
        self, doc1: dict[str, Any], doc2: dict[str, Any], target_topics: set[str]
    ) -> float:
        """Calculate relevance score between two documents.

        Args:
            doc1: First document (target)
            doc2: Second document (candidate)
            target_topics: Combined topics from target document

        Returns:
            Relevance score (0-1)
        """
        score = 0.0

        # Get topics from candidate document
        doc2_intelligence = doc2.get("intelligence", {})
        doc2_topics = set(doc2_intelligence.get("extracted_topics", []))
        doc2_metadata_topics = set(doc2.get("metadata", {}).get("topics", []))
        all_doc2_topics = doc2_topics | doc2_metadata_topics

        # Topic overlap score (40% weight)
        if target_topics and all_doc2_topics:
            topic_overlap = len(target_topics & all_doc2_topics)
            topic_union = len(target_topics | all_doc2_topics)
            topic_similarity = topic_overlap / topic_union if topic_union > 0 else 0
            score += topic_similarity * 0.4

        # Path similarity score (20% weight)
        path_similarity = self._calculate_path_similarity(doc1, doc2)
        score += path_similarity * 0.2

        # Content fingerprint similarity (25% weight)
        fingerprint_similarity = self._calculate_fingerprint_similarity(doc1, doc2)
        score += fingerprint_similarity * 0.25

        # Quality compatibility score (15% weight)
        quality_compatibility = self._calculate_quality_compatibility(doc1, doc2)
        score += quality_compatibility * 0.15

        return min(score, 1.0)

    def _determine_relationship_type(
        self, doc1: dict[str, Any], doc2: dict[str, Any], relevance: float
    ) -> str:
        """Determine the type of relationship between documents.

        Args:
            doc1: First document
            doc2: Second document
            relevance: Calculated relevance score

        Returns:
            Relationship type string
        """
        # Check for hierarchical relationship based on paths
        path1 = doc1.get("metadata", {}).get("source", {}).get("path", "")
        path2 = doc2.get("metadata", {}).get("source", {}).get("path", "")

        if path1 and path2:
            if path2.startswith(path1.rsplit("/", 1)[0]):
                return "sibling"
            elif path1.startswith(path2.rsplit("/", 1)[0]):
                return "parent-child"

        # Check for complementary content
        doc1_intelligence = doc1.get("intelligence", {})
        doc2_intelligence = doc2.get("intelligence", {})

        doc1_topics = set(doc1_intelligence.get("extracted_topics", []))
        doc2_topics = set(doc2_intelligence.get("extracted_topics", []))

        # If high topic overlap, it's related content
        if doc1_topics and doc2_topics:
            overlap_ratio = len(doc1_topics & doc2_topics) / len(
                doc1_topics | doc2_topics
            )
            if overlap_ratio > 0.6:
                return "related-content"

        # Check for implementation vs concept relationship
        if any(
            topic in ["implementation", "example", "tutorial"] for topic in doc1_topics
        ):
            if any(
                topic in ["concept", "overview", "introduction"]
                for topic in doc2_topics
            ):
                return "implementation-detail"

        # High relevance but no specific pattern
        if relevance > 0.8:
            return "highly-related"
        elif relevance > 0.6:
            return "related"
        else:
            return "tangentially-related"

    def _calculate_path_similarity(
        self, doc1: dict[str, Any], doc2: dict[str, Any]
    ) -> float:
        """Calculate similarity based on file paths."""
        path1 = doc1.get("metadata", {}).get("source", {}).get("path", "")
        path2 = doc2.get("metadata", {}).get("source", {}).get("path", "")

        if not path1 or not path2:
            return 0.0

        # Split paths into components
        parts1 = path1.replace("\\", "/").split("/")
        parts2 = path2.replace("\\", "/").split("/")

        # Calculate common path prefix length
        common_prefix = 0
        for p1, p2 in zip(parts1, parts2, strict=False):
            if p1 == p2:
                common_prefix += 1
            else:
                break

        # Calculate similarity based on shared path depth
        max_depth = max(len(parts1), len(parts2))
        if max_depth == 0:
            return 0.0

        return common_prefix / max_depth

    def _calculate_fingerprint_similarity(
        self, doc1: dict[str, Any], doc2: dict[str, Any]
    ) -> float:
        """Calculate similarity based on content fingerprints."""
        fingerprint1 = doc1.get("intelligence", {}).get("content_fingerprint", "")
        fingerprint2 = doc2.get("intelligence", {}).get("content_fingerprint", "")

        if not fingerprint1 or not fingerprint2:
            return 0.0

        # Simple fingerprint similarity (could be enhanced with more sophisticated methods)
        if fingerprint1 == fingerprint2:
            return 1.0

        # Calculate character-level similarity for fingerprints
        matches = sum(
            1 for c1, c2 in zip(fingerprint1, fingerprint2, strict=False) if c1 == c2
        )
        max_length = max(len(fingerprint1), len(fingerprint2))

        return matches / max_length if max_length > 0 else 0.0

    def _calculate_quality_compatibility(
        self, doc1: dict[str, Any], doc2: dict[str, Any]
    ) -> float:
        """Calculate compatibility based on quality scores."""
        quality1 = doc1.get("intelligence", {}).get("quality_metrics", {})
        quality2 = doc2.get("intelligence", {}).get("quality_metrics", {})

        if not quality1 or not quality2:
            return 0.5  # Neutral if no quality data

        # Documents with similar quality levels are more compatible
        overall1 = quality1.get("overall", 0.5)
        overall2 = quality2.get("overall", 0.5)

        # Calculate similarity in quality (closer scores = higher compatibility)
        quality_diff = abs(overall1 - overall2)
        compatibility = 1.0 - quality_diff

        return max(0.0, compatibility)
