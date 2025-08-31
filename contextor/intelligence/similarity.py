"""Document similarity analysis and duplicate detection."""

import hashlib
import re
from collections import Counter
from typing import Any

import structlog

logger = structlog.get_logger()


class SimilarityAnalyzer:
    """Analyzes document similarity and detects duplicates."""

    def __init__(self, config: dict[str, Any] = None):
        """Initialize the similarity analyzer.

        Args:
            config: Configuration for similarity analysis
        """
        self.config = config or {}
        self.similarity_threshold = self.config.get("similarity_threshold", 0.8)
        self.duplicate_threshold = self.config.get("duplicate_threshold", 0.95)

    def generate_fingerprint(self, content: str) -> str:
        """Generate a content fingerprint for similarity comparison.

        Args:
            content: Document content text

        Returns:
            Content fingerprint hash
        """
        # Normalize content for fingerprinting
        normalized = self._normalize_content(content)

        # Generate hash
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def find_similar_documents(
        self, documents: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Find similar documents in a collection.

        Args:
            documents: List of document data dictionaries

        Returns:
            Dictionary mapping document slugs to lists of similar documents
        """
        similarities = {}

        # Generate content vectors for all documents
        doc_vectors = {}
        for doc in documents:
            vector = self._generate_content_vector(doc["content"])
            doc_vectors[doc["slug"]] = vector

        # Compare all pairs of documents
        for i, doc1 in enumerate(documents):
            similar_docs = []

            for j, doc2 in enumerate(documents):
                if i >= j:  # Skip self and already compared pairs
                    continue

                similarity = self._calculate_similarity(
                    doc_vectors[doc1["slug"]], doc_vectors[doc2["slug"]]
                )

                if similarity >= self.similarity_threshold:
                    relationship_type = (
                        "duplicate"
                        if similarity >= self.duplicate_threshold
                        else "similar"
                    )

                    similar_docs.append(
                        {
                            "slug": doc2["slug"],
                            "title": doc2["title"],
                            "similarity": round(similarity, 3),
                            "relationship": relationship_type,
                        }
                    )

            if similar_docs:
                # Sort by similarity score
                similar_docs.sort(key=lambda x: x["similarity"], reverse=True)
                similarities[doc1["slug"]] = similar_docs

        logger.debug(
            "Similarity analysis complete",
            total_documents=len(documents),
            documents_with_similarities=len(similarities),
        )

        return similarities

    def _normalize_content(self, content: str) -> str:
        """Normalize content for consistent fingerprinting."""
        # Convert to lowercase
        normalized = content.lower()

        # Remove markdown formatting
        normalized = re.sub(r"[*_#>`-]", "", normalized)

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        # Remove punctuation except periods
        normalized = re.sub(r"[^\w\s.]", "", normalized)

        return normalized.strip()

    def _generate_content_vector(self, content: str) -> Counter:
        """Generate a word frequency vector for content.

        Args:
            content: Document content text

        Returns:
            Counter with word frequencies
        """
        # Clean content
        cleaned = self._clean_content_for_vector(content)

        # Extract words (3+ characters)
        words = re.findall(r"\b[a-zA-Z]{3,}\b", cleaned.lower())

        # Filter common stop words
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "its",
            "may",
            "new",
            "now",
            "old",
            "see",
            "two",
            "who",
            "boy",
            "did",
            "use",
            "way",
            "she",
            "oil",
            "sit",
            "set",
            "run",
            "eat",
            "far",
            "sea",
            "eye",
            "ask",
            "own",
            "say",
            "too",
            "any",
            "try",
            "let",
            "put",
        }

        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]

        return Counter(filtered_words)

    def _clean_content_for_vector(self, content: str) -> str:
        """Clean content for vector generation."""
        # Remove code blocks
        content = re.sub(r"```[\s\S]*?```", " ", content)
        content = re.sub(r"`[^`]+`", " ", content)

        # Remove links but keep link text
        content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)

        # Remove HTML tags
        content = re.sub(r"<[^>]+>", " ", content)

        # Remove markdown headers but keep text
        content = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)

        # Normalize whitespace
        content = re.sub(r"\s+", " ", content)

        return content.strip()

    def _calculate_similarity(self, vector1: Counter, vector2: Counter) -> float:
        """Calculate cosine similarity between two word vectors.

        Args:
            vector1: First document word vector
            vector2: Second document word vector

        Returns:
            Cosine similarity score (0-1)
        """
        if not vector1 or not vector2:
            return 0.0

        # Get intersection of words
        common_words = set(vector1.keys()) & set(vector2.keys())

        if not common_words:
            return 0.0

        # Calculate dot product
        dot_product = sum(vector1[word] * vector2[word] for word in common_words)

        # Calculate magnitudes
        magnitude1 = sum(count**2 for count in vector1.values()) ** 0.5
        magnitude2 = sum(count**2 for count in vector2.values()) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)

        return max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
