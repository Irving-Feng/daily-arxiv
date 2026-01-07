"""
Formatter for converting processed papers to Notion blocks.
Handles both detailed and basic paper formats.
"""
from typing import List, Dict, Any
from dataclasses import dataclass
from loguru import logger

from src.notion.blocks import (
    create_paper_blocks,
    create_heading_block,
    create_paragraph_block,
    create_divider_block
)
from src.llm.openai_client import DetailedReport


@dataclass
class ProcessedPaper:
    """A processed paper ready for Notion upload."""
    rank: int
    title: str
    chinese_title: str
    authors: List[str]
    chinese_abstract: str
    pdf_url: str
    detailed_report: DetailedReport | None = None
    basic_summary: str | None = None


class NotionFormatter:
    """Formats processed papers into Notion blocks."""

    @staticmethod
    def format_daily_papers(papers: List[ProcessedPaper], date: str) -> List[Dict[str, Any]]:
        """
        Format daily papers into Notion blocks.

        Args:
            papers: List of processed papers
            date: Date string for page title

        Returns:
            List of Notion blocks
        """
        logger.info(f"Formatting {len(papers)} papers for Notion")

        blocks = []

        # Page title
        title = f"Daily arXiv (cs.CL) - {date}"
        blocks.append(create_heading_block(title, level=1))

        # Add divider
        blocks.append(create_divider_block())

        # Add each paper
        for paper in papers:
            paper_blocks = create_paper_blocks(
                index=paper.rank,
                title=paper.title,
                authors=paper.authors,
                chinese_abstract=paper.chinese_abstract,
                pdf_url=paper.pdf_url,
                detailed_report=paper.detailed_report
            )
            blocks.extend(paper_blocks)

        logger.info(f"Created {len(blocks)} Notion blocks")
        return blocks

    @staticmethod
    def format_weekly_summary(summary_text: str, week_start: str, week_end: str) -> List[Dict[str, Any]]:
        """
        Format weekly summary into Notion blocks.

        Args:
            summary_text: Generated summary text
            week_start: Week start date
            week_end: Week end date

        Returns:
            List of Notion blocks
        """
        logger.info(f"Formatting weekly summary for {week_start} to {week_end}")

        blocks = []

        # Title
        title = f"Weekly Summary ({week_start} to {week_end})"
        blocks.append(create_heading_block(title, level=1))

        # Summary content
        blocks.append(create_paragraph_block(summary_text))

        logger.info(f"Created {len(blocks)} Notion blocks for weekly summary")
        return blocks

    @staticmethod
    def format_monthly_summary(summary_text: str, month: str, year: int) -> List[Dict[str, Any]]:
        """
        Format monthly summary into Notion blocks.

        Args:
            summary_text: Generated summary text
            month: Month name
            year: Year

        Returns:
            List of Notion blocks
        """
        logger.info(f"Formatting monthly summary for {month} {year}")

        blocks = []

        # Title
        title = f"Monthly Summary - {month} {year}"
        blocks.append(create_heading_block(title, level=1))

        # Summary content
        blocks.append(create_paragraph_block(summary_text))

        logger.info(f"Created {len(blocks)} Notion blocks for monthly summary")
        return blocks
