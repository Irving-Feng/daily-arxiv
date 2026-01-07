"""
Summarizer for generating weekly and monthly trend reports.
Analyzes papers and generates LLM-based summaries.
"""
from typing import List, Tuple
from collections import Counter
from loguru import logger

from src.arxiv.arxiv_client import PaperMetadata
from src.llm.openai_client import OpenAIClient


class TrendAnalyzer:
    """Analyzes trends in collected papers."""

    def __init__(self, llm_client: OpenAIClient):
        """
        Initialize trend analyzer.

        Args:
            llm_client: OpenAI client for generating summaries
        """
        self.llm_client = llm_client

    def analyze_trends(self, papers: List[PaperMetadata]) -> dict:
        """
        Analyze trends in a collection of papers.

        Args:
            papers: List of paper metadata

        Returns:
            Dictionary with trend statistics
        """
        logger.info(f"Analyzing trends for {len(papers)} papers")

        # Category frequency
        category_counts = Counter()
        for paper in papers:
            for cat in paper.categories:
                category_counts[cat] += 1

        # Top categories
        top_categories = category_counts.most_common(10)

        # Simple keyword extraction from titles
        keywords = self._extract_keywords(papers)

        logger.info(f"Found {len(top_categories)} categories, {len(keywords)} keywords")

        return {
            "total_papers": len(papers),
            "categories": dict(top_categories),
            "top_keywords": keywords[:20]
        }

    def _extract_keywords(self, papers: List[PaperMetadata]) -> List[Tuple[str, int]]:
        """
        Extract common keywords from paper titles.

        Args:
            papers: List of paper metadata

        Returns:
            List of (keyword, count) tuples
        """
        # Common technical terms to ignore
        stop_words = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "via", "using", "based", "model",
            "learning", "approach", "method", "system", "study", "analysis",
            "paper", "research", "new", "novel", "efficient", "robust"
        }

        # Simple word extraction
        word_counts = Counter()

        for paper in papers:
            # Extract words from title (lowercase, alphanumeric only)
            words = paper.title.lower().split()

            for word in words:
                # Clean word
                word = ''.join(c for c in word if c.isalnum())

                # Filter
                if len(word) > 3 and word not in stop_words:
                    word_counts[word] += 1

        # Return top keywords
        return word_counts.most_common(50)

    def generate_weekly_summary(
        self,
        papers: List[PaperMetadata],
        week_start: str,
        week_end: str
    ) -> str:
        """
        Generate weekly summary report.

        Args:
            papers: List of papers from the week
            week_start: Week start date
            week_end: Week end date

        Returns:
            Weekly summary text in Chinese
        """
        logger.info(f"Generating weekly summary for {week_start} to {week_end}")

        # Analyze trends
        trends = self.analyze_trends(papers)

        # Format for LLM
        trending_categories = ", ".join([
            f"{cat} ({count})"
            for cat, count in trends["categories"].items()
        ])

        top_keywords = ", ".join([
            f"{kw} ({count})"
            for kw, count in trends["top_keywords"][:10]
        ])

        # Get interest-matching papers
        interest_papers = [p for p in papers if p.match_score > 0]
        interest_papers.sort(key=lambda p: p.match_score, reverse=True)

        interest_summary = self._format_papers_for_summary(interest_papers[:10])

        # Generate LLM summary
        summary = self.llm_client.generate_weekly_summary(
            period_start=week_start,
            period_end=week_end,
            total_papers=len(papers),
            trending_categories=trending_categories,
            top_keywords=top_keywords,
            interest_papers_summary=interest_summary
        )

        logger.info("Weekly summary generated")
        return summary

    def generate_monthly_summary(
        self,
        papers: List[PaperMetadata],
        month: str,
        year: int
    ) -> str:
        """
        Generate monthly summary report.

        Args:
            papers: List of papers from the month
            month: Month name
            year: Year

        Returns:
            Monthly summary text in Chinese
        """
        logger.info(f"Generating monthly summary for {month} {year}")

        # Analyze trends
        trends = self.analyze_trends(papers)

        # Format category distribution
        category_distribution = "\n".join([
            f"  {cat}: {count}"
            for cat, count in trends["categories"].items()
        ])

        # Get outstanding papers (top by match score)
        outstanding_papers = sorted(
            papers,
            key=lambda p: p.match_score,
            reverse=True
        )[:20]

        outstanding_summary = self._format_papers_for_summary(outstanding_papers)

        # Generate LLM summary
        summary = self.llm_client.generate_monthly_summary(
            month=month,
            year=year,
            total_papers=len(papers),
            category_distribution=category_distribution,
            outstanding_papers=outstanding_summary
        )

        logger.info("Monthly summary generated")
        return summary

    def _format_papers_for_summary(self, papers: List[PaperMetadata]) -> str:
        """
        Format papers for LLM summary input.

        Args:
            papers: List of papers

        Returns:
            Formatted string
        """
        formatted = []

        for i, paper in enumerate(papers, 1):
            entry = (
                f"{i}. {paper.title}\n"
                f"   Authors: {', '.join(paper.authors[:3])}\n"
                f"   Categories: {', '.join(paper.categories)}\n"
            )
            formatted.append(entry)

        return "\n".join(formatted)
