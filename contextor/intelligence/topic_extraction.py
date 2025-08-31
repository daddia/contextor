"""Topic extraction from document content and metadata."""

import re
from collections import Counter
from typing import Any, Optional

import structlog

logger = structlog.get_logger()


class TopicExtractor:
    """Extracts topics from document content using keywords and headings."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the topic extractor.

        Args:
            config: Configuration for topic extraction
        """
        self.config = config or {}
        self.max_topics = self.config.get("max_topics", 10)
        self.min_topic_frequency = self.config.get("min_frequency", 2)

        # Common stop words to filter out
        self.stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "against",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "her",
            "its",
            "our",
            "their",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "now",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "what",
            "which",
            "who",
            "whom",
            "whose",
            "if",
            "then",
            "else",
        }

    def extract_topics(self, content: str, metadata: dict[str, Any]) -> list[str]:
        """Extract topics from document content and metadata.

        Args:
            content: Document content text
            metadata: Document metadata dictionary

        Returns:
            List of extracted topic strings
        """
        topics = set()

        # Extract from path-based topics
        path_topics = self._extract_from_path(
            metadata.get("source", {}).get("path", "")
        )
        topics.update(path_topics)

        # Extract from headings
        heading_topics = self._extract_from_headings(content)
        topics.update(heading_topics)

        # Extract from content keywords
        keyword_topics = self._extract_from_keywords(content)
        topics.update(keyword_topics)

        # Extract from metadata
        metadata_topics = self._extract_from_metadata(metadata)
        topics.update(metadata_topics)

        # Filter and rank topics
        filtered_topics = self._filter_and_rank_topics(list(topics), content)

        logger.debug(
            "Extracted topics",
            total_candidates=len(topics),
            filtered_count=len(filtered_topics),
            topics=filtered_topics[:5],  # Log first 5 for debugging
        )

        return filtered_topics[: self.max_topics]

    def _extract_from_path(self, path: str) -> list[str]:
        """Extract topics from file path components."""
        if not path:
            return []

        topics = []

        # Split path and extract meaningful segments
        path_parts = path.replace("\\", "/").split("/")

        for part in path_parts:
            # Remove file extension
            part = re.sub(r"\.[^.]+$", "", part)

            # Split on common separators and extract words
            words = re.split(r"[-_\s]+", part.lower())

            for word in words:
                if len(word) > 2 and word not in self.stop_words:
                    topics.append(word)

        return topics

    def _extract_from_headings(self, content: str) -> list[str]:
        """Extract topics from markdown headings."""
        topics = []

        # Find all markdown headings
        heading_pattern = r"^#+\s+(.+)$"
        headings = re.findall(heading_pattern, content, re.MULTILINE)

        for heading in headings:
            # Clean heading text and extract keywords
            cleaned = re.sub(r"[^\w\s-]", " ", heading.lower())
            words = cleaned.split()

            for word in words:
                if len(word) > 2 and word not in self.stop_words:
                    topics.append(word)

        return topics

    def _extract_from_keywords(self, content: str) -> list[str]:
        """Extract topics from content keywords using frequency analysis."""
        # Clean content: remove code blocks, links, etc.
        cleaned_content = self._clean_content_for_analysis(content)

        # Extract words
        words = re.findall(r"\b[a-zA-Z]{3,}\b", cleaned_content.lower())

        # Filter stop words and count frequency
        filtered_words = [w for w in words if w not in self.stop_words]
        word_freq = Counter(filtered_words)

        # Return words that appear frequently enough
        topics = [
            word for word, freq in word_freq.items() if freq >= self.min_topic_frequency
        ]

        return topics

    def _extract_from_metadata(self, metadata: dict[str, Any]) -> list[str]:
        """Extract topics from document metadata."""
        topics = []

        # Extract from existing topics
        existing_topics = metadata.get("topics", [])
        if existing_topics:
            topics.extend(existing_topics)

        # Extract from title
        title = metadata.get("title", "")
        if title:
            title_words = re.findall(r"\b[a-zA-Z]{3,}\b", title.lower())
            topics.extend([w for w in title_words if w not in self.stop_words])

        return topics

    def _clean_content_for_analysis(self, content: str) -> str:
        """Clean content for keyword analysis."""
        # Remove code blocks
        content = re.sub(r"```[\s\S]*?```", " ", content)
        content = re.sub(r"`[^`]+`", " ", content)

        # Remove links
        content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)

        # Remove markdown formatting
        content = re.sub(r"[*_#>-]", " ", content)

        # Remove HTML tags
        content = re.sub(r"<[^>]+>", " ", content)

        # Normalize whitespace
        content = re.sub(r"\s+", " ", content)

        return content.strip()

    def _filter_and_rank_topics(self, topics: list[str], content: str) -> list[str]:
        """Filter and rank topics by relevance."""
        if not topics:
            return []

        # Count topic frequency in content
        content_lower = content.lower()
        topic_scores = {}

        for topic in set(topics):  # Remove duplicates
            # Count occurrences in content
            frequency = content_lower.count(topic.lower())

            # Boost score for topics that appear in headings
            heading_boost = 2 if self._appears_in_headings(topic, content) else 1

            # Boost score for longer, more specific terms
            length_boost = min(len(topic) / 5, 2)

            topic_scores[topic] = frequency * heading_boost * length_boost

        # Sort by score and return top topics
        ranked_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

        return [topic for topic, score in ranked_topics if score > 0]

    def _appears_in_headings(self, topic: str, content: str) -> bool:
        """Check if topic appears in any heading."""
        heading_pattern = r"^#+\s+(.+)$"
        headings = re.findall(heading_pattern, content, re.MULTILINE)

        for heading in headings:
            if topic.lower() in heading.lower():
                return True

        return False
