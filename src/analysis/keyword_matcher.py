"""
Keyword matching for detecting papers of interest.
Matches user interests against paper titles, abstracts, and categories.
"""
import re
from typing import List, Set
from loguru import logger

from src.arxiv.arxiv_client import PaperMetadata


class KeywordMatcher:
    """Matches papers against user interests using keyword detection."""

    # Scoring weights
    TITLE_WEIGHT = 3.0
    ABSTRACT_WEIGHT = 2.0
    CATEGORY_WEIGHT = 1.0

    def __init__(self, interests: List[str]):
        """
        Initialize keyword matcher with user interests.

        Args:
            interests: List of interest topics (e.g., ["agents", "reinforcement learning"])
        """
        self.interests = interests
        self.expanded_keywords = self._expand_keywords(interests)
        logger.info(f"Initialized KeywordMatcher with {len(interests)} interests")
        logger.debug(f"Expanded keywords: {self.expanded_keywords}")

    def _expand_keywords(self, interests: List[str]) -> Set[str]:
        """
        Generate keyword variations for matching.

        Creates variations including:
        - Original keyword
        - Hyphenated/space-separated variants
        - Singular/plural forms

        Args:
            interests: Original interest keywords

        Returns:
            Set of expanded keyword variations
        """
        expanded = set()

        for interest in interests:
            # Normalize: lowercase, strip extra spaces
            normalized = interest.lower().strip()

            # Add original
            expanded.add(normalized)

            # Add space/hyphen variants
            if ' ' in normalized:
                expanded.add(normalized.replace(' ', '-'))
            elif '-' in normalized:
                expanded.add(normalized.replace('-', ' '))

            # Add singular/plural variants
            if normalized.endswith('s'):
                # Remove 's' for singular
                singular = normalized[:-1]
                expanded.add(singular)
            else:
                # Add 's' for plural (simple heuristic)
                plural = normalized + 's'
                expanded.add(plural)

        return expanded

    def find_matches(self, papers: List[PaperMetadata]) -> List[PaperMetadata]:
        """
        Find papers that match user interests.

        Args:
            papers: List of paper metadata

        Returns:
            List of papers with match_score set, sorted by score (descending)
        """
        matches = []

        for paper in papers:
            score = self._calculate_match_score(paper)
            if score > 0:
                paper.match_score = score
                matches.append(paper)
                logger.debug(
                    f"Paper matched: '{paper.title[:50]}...' "
                    f"(score: {score:.2f})"
                )

        # Sort by match score (highest first)
        matches.sort(key=lambda p: p.match_score, reverse=True)

        logger.info(f"Found {len(matches)} papers matching user interests")
        return matches

    def _calculate_match_score(self, paper: PaperMetadata) -> float:
        """
        Calculate match score for a paper.

        Score = (title_matches * TITLE_WEIGHT) +
                (abstract_matches * ABSTRACT_WEIGHT) +
                (category_matches * CATEGORY_WEIGHT)

        Args:
            paper: Paper metadata

        Returns:
            Match score (0 if no matches)
        """
        score = 0.0

        # Check title (highest weight)
        title_score = self._check_match(paper.title)
        score += title_score * self.TITLE_WEIGHT

        # Check abstract (medium weight)
        abstract_score = self._check_match(paper.summary)
        score += abstract_score * self.ABSTRACT_WEIGHT

        # Check categories (lowest weight)
        category_score = self._check_match(' '.join(paper.categories))
        score += category_score * self.CATEGORY_WEIGHT

        return score

    def _check_match(self, text: str) -> float:
        """
        Check if text matches any expanded keywords.

        Returns a score based on the number and quality of matches:
        - 1.0 for single keyword match
        - 2.0 for compound phrase match (e.g., "agentic memory")
        - Additional 0.5 for each additional match

        Args:
            text: Text to check (case-insensitive)

        Returns:
            Match score (0 if no match)
        """
        text_lower = text.lower()
        score = 0.0

        # Check for simple keyword matches
        simple_matches = 0
        for keyword in self.expanded_keywords:
            if keyword in text_lower:
                simple_matches += 1

        if simple_matches > 0:
            # Base score for matches
            score = float(simple_matches)

        # Check for compound phrase matches (multi-word interests)
        for interest in self.interests:
            interest_normalized = interest.lower().strip()
            if ' ' in interest_normalized or '-' in interest_normalized:
                # Normalize for matching (spaces and hyphens)
                variants = [
                    interest_normalized.replace(' ', ' '),  # Original
                    interest_normalized.replace(' ', '-'),  # Hyphenated
                    interest_normalized.replace('-', ' '),  # Space-separated
                ]

                for variant in variants:
                    # Use word boundaries for phrase matching
                    pattern = r'\b' + re.escape(variant) + r'\b'
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        # Bonus for compound phrase match
                        score += 1.0
                        break

        return score

    def get_top_matches(self, papers: List[PaperMetadata], top_n: int = 10) -> List[PaperMetadata]:
        """
        Get top N matching papers.

        Args:
            papers: List of paper metadata
            top_n: Number of top matches to return

        Returns:
            List of top N papers sorted by match score
        """
        matches = self.find_matches(papers)
        return matches[:top_n]
