"""Quality scoring for document content."""

import re
from datetime import UTC, datetime
from typing import Any, Optional

import structlog

logger = structlog.get_logger()


class QualityScorer:
    """Scores document quality based on completeness, freshness, and clarity."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """Initialize the quality scorer.

        Args:
            config: Configuration for quality scoring
        """
        self.config = config or {}
        self.completeness_weight = self.config.get("completeness_weight", 0.4)
        self.freshness_weight = self.config.get("freshness_weight", 0.3)
        self.clarity_weight = self.config.get("clarity_weight", 0.3)

    def score_quality(self, content: str, metadata: dict[str, Any]) -> dict[str, float]:
        """Score document quality across multiple dimensions.

        Args:
            content: Document content text
            metadata: Document metadata dictionary

        Returns:
            Dictionary with quality scores and overall score
        """
        completeness = self._score_completeness(content, metadata)
        freshness = self._score_freshness(metadata)
        clarity = self._score_clarity(content)

        # Calculate weighted overall score
        overall = (
            completeness * self.completeness_weight
            + freshness * self.freshness_weight
            + clarity * self.clarity_weight
        )

        quality_metrics = {
            "completeness": round(completeness, 2),
            "freshness": round(freshness, 2),
            "clarity": round(clarity, 2),
            "overall": round(overall, 2),
        }

        logger.debug("Quality scoring complete", **quality_metrics)

        return quality_metrics

    def _score_completeness(self, content: str, metadata: dict[str, Any]) -> float:
        """Score document completeness based on structure and content."""
        score = 0.0

        # Check for title
        if metadata.get("title"):
            score += 0.2

        # Check for headings structure
        headings = re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)
        if len(headings) >= 2:
            score += 0.3
        elif len(headings) >= 1:
            score += 0.15

        # Check content length (not too short, not extremely long)
        word_count = len(content.split())
        if 100 <= word_count <= 5000:
            score += 0.2
        elif 50 <= word_count < 100 or 5000 < word_count <= 10000:
            score += 0.1

        # Check for code examples
        code_blocks = re.findall(r"```[\s\S]*?```", content)
        inline_code = re.findall(r"`[^`]+`", content)
        if code_blocks or len(inline_code) >= 3:
            score += 0.15

        # Check for links (external references)
        links = re.findall(r"\[([^\]]+)\]\([^\)]+\)", content)
        if len(links) >= 2:
            score += 0.15
        elif len(links) >= 1:
            score += 0.1

        return min(score, 1.0)

    def _score_freshness(self, metadata: dict[str, Any]) -> float:
        """Score document freshness based on timestamps."""
        try:
            # Get the fetched_at timestamp
            fetched_at_str = metadata.get("fetched_at")
            if not fetched_at_str:
                return 0.5  # Unknown freshness

            # Parse timestamp
            if fetched_at_str.endswith("Z"):
                fetched_at_str = fetched_at_str[:-1] + "+00:00"

            fetched_at = datetime.fromisoformat(fetched_at_str)
            if fetched_at.tzinfo is None:
                fetched_at = fetched_at.replace(tzinfo=UTC)

            now = datetime.now(UTC)
            days_old = (now - fetched_at).days

            # Score based on age
            if days_old <= 30:
                return 1.0  # Very fresh
            elif days_old <= 90:
                return 0.8  # Fresh
            elif days_old <= 180:
                return 0.6  # Moderately fresh
            elif days_old <= 365:
                return 0.4  # Aging
            else:
                return 0.2  # Old

        except Exception as e:
            logger.debug("Failed to parse freshness timestamp", error=str(e))
            return 0.5  # Unknown freshness

    def _score_clarity(self, content: str) -> float:
        """Score document clarity based on readability metrics."""
        score = 0.0

        # Check for clear paragraph structure
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if len(paragraphs) >= 3:
            score += 0.2
        elif len(paragraphs) >= 2:
            score += 0.1

        # Check for reasonable sentence length
        sentences = re.split(r"[.!?]+", content)
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]

        if sentence_lengths:
            avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
            # Optimal range is 15-25 words per sentence
            if 15 <= avg_sentence_length <= 25:
                score += 0.3
            elif 10 <= avg_sentence_length < 15 or 25 < avg_sentence_length <= 35:
                score += 0.2
            elif 5 <= avg_sentence_length < 10 or 35 < avg_sentence_length <= 50:
                score += 0.1

        # Check for lists and structured content
        bullet_lists = re.findall(r"^[-*+]\s+", content, re.MULTILINE)
        numbered_lists = re.findall(r"^\d+\.\s+", content, re.MULTILINE)

        if len(bullet_lists) >= 3 or len(numbered_lists) >= 3:
            score += 0.2
        elif len(bullet_lists) >= 1 or len(numbered_lists) >= 1:
            score += 0.1

        # Check for excessive complexity indicators
        # Penalize very long words or excessive jargon
        words = content.split()
        long_words = [w for w in words if len(w) > 12]
        long_word_ratio = len(long_words) / len(words) if words else 0

        if long_word_ratio < 0.05:  # Less than 5% long words
            score += 0.2
        elif long_word_ratio < 0.1:  # Less than 10% long words
            score += 0.1

        # Check for good use of formatting
        bold_text = re.findall(r"\*\*[^*]+\*\*", content)
        italic_text = re.findall(r"\*[^*]+\*", content)

        if len(bold_text) >= 2 or len(italic_text) >= 2:
            score += 0.1

        return min(score, 1.0)
