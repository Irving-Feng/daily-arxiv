#!/usr/bin/env python3
"""
Main entry point for Daily arXiv Paper Collection System.
Orchestrates the entire pipeline from scraping to Notion upload.
"""
import argparse
import sys
from pathlib import Path
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_settings
from src.utils.logger import setup_logging
from src.utils.date_utils import (
    get_previous_day_beijing,
    get_week_start_end,
    get_month_start_end,
    is_last_day_of_month
)
from src.scrapers.papers_cool_scraper import PapersCoolScraper
from src.arxiv.arxiv_client import ArxivClient, PaperMetadata
from src.analysis.keyword_matcher import KeywordMatcher
from src.pdf.downloader import PDFDownloader
from src.pdf.parser import PDFParser
from src.llm.openai_client import OpenAIClient
from src.notion.client import NotionAPI
from src.notion.formatter import NotionFormatter, ProcessedPaper
from src.analysis.summarizer import TrendAnalyzer


def daily_collection_job(target_date: str | None = None) -> None:
    """
    Execute daily paper collection and processing.

    Args:
        target_date: Target date in YYYY-MM-DD format (None for yesterday)
    """
    logger.info("=" * 60)
    logger.info("Starting Daily arXiv Paper Collection")
    logger.info("=" * 60)

    # Load settings
    settings = get_settings()

    # Determine target date
    if target_date is None:
        target_date = get_previous_day_beijing()

    logger.info(f"Target date: {target_date}")

    try:
        # Step 1: Scrape papers.cool for rankings
        logger.info("Step 1: Fetching paper rankings from papers.cool")
        scraper = PapersCoolScraper()
        ranked_papers = scraper.fetch_ranked_papers(
            target_date=target_date,
            category=settings.arxiv_category
        )

        if not ranked_papers:
            logger.warning(f"No papers found for {target_date}")
            return

        logger.info(f"Found {len(ranked_papers)} ranked papers")

        # Step 2: Fetch full metadata from arXiv
        logger.info("Step 2: Fetching full metadata from arXiv API")
        arxiv_client = ArxivClient()
        paper_ids = [p.paper_id for p in ranked_papers]
        all_papers = arxiv_client.get_papers_by_ids(paper_ids)

        logger.info(f"Retrieved metadata for {len(all_papers)} papers")

        # Step 3: Match against user interests
        logger.info("Step 3: Matching papers against user interests")
        matcher = KeywordMatcher(interests=settings.interests_list)
        interest_papers = matcher.find_matches(all_papers)

        logger.info(f"Found {len(interest_papers)} interest-matching papers")

        # Step 4: Prioritize papers
        logger.info("Step 4: Prioritizing papers")
        processed_papers = prioritize_papers(
            ranked_papers=ranked_papers,
            all_papers=all_papers,
            interest_papers=interest_papers,
            top_n=settings.top_papers_count
        )

        logger.info(f"Processing {len(processed_papers)} papers with detailed reports")

        # Step 5: Initialize components
        llm_client = OpenAIClient(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.openai_model,
            max_tokens=settings.openai_max_tokens,
            temperature=settings.openai_temperature
        )

        pdf_downloader = PDFDownloader(max_size_mb=settings.max_pdf_size_mb)
        pdf_parser = PDFParser()

        # Step 6: Process papers
        logger.info("Step 5: Processing papers with LLM")
        final_papers = []

        for paper_info in processed_papers:
            paper = paper_info["paper"]
            needs_detailed = paper_info["needs_detailed_report"]
            rank = paper_info["rank"]

            logger.info(f"Processing paper #{rank}: {paper.title[:50]}...")

            # Translate title and abstract
            chinese_title = llm_client.translate_title(paper.title)
            chinese_abstract = llm_client.translate_abstract(paper.summary)

            # Detailed report if needed
            detailed_report = None
            basic_summary = None

            if needs_detailed:
                # Download and parse PDF
                pdf_path = pdf_downloader.download_paper(paper.pdf_url, paper.paper_id)

                if pdf_path:
                    try:
                        # Extract text
                        pdf_text = pdf_parser.extract_text_smart(pdf_path)

                        # Generate detailed report
                        detailed_report = llm_client.generate_detailed_report(
                            title=paper.title,
                            abstract=paper.summary,
                            pdf_text=pdf_text
                        )

                        logger.info(f"Generated detailed report for {paper.paper_id}")

                    finally:
                        # Cleanup PDF
                        pdf_downloader.cleanup(paper.paper_id)
                else:
                    logger.warning(f"Could not download PDF for {paper.paper_id}, using basic summary")
                    basic_summary = llm_client.generate_basic_summary(paper.title, paper.summary)

            if not detailed_report and not basic_summary:
                basic_summary = llm_client.generate_basic_summary(paper.title, paper.summary)

            # Create processed paper
            processed = ProcessedPaper(
                rank=rank,
                title=paper.title,
                chinese_title=chinese_title,
                authors=paper.authors,
                chinese_abstract=chinese_abstract,
                pdf_url=paper.pdf_url,
                detailed_report=detailed_report,
                basic_summary=basic_summary
            )

            final_papers.append(processed)

        # Step 7: Upload to Notion
        logger.info("Step 6: Uploading to Notion")
        notion_client = NotionAPI(
            api_key=settings.notion_api_key,
            database_id=settings.notion_database_id,
            parent_page_id=settings.notion_parent_page_id
        )

        # Format blocks
        formatter = NotionFormatter()
        blocks = formatter.format_daily_papers(final_papers, target_date)

        # Upload
        notion_client.upload_daily_papers(blocks, target_date)

        logger.info("=" * 60)
        logger.info(f"Successfully processed {len(final_papers)} papers")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Daily collection failed: {e}")
        raise


def weekly_summary_job(target_date: str | None = None) -> None:
    """
    Execute weekly summary generation.

    Args:
        target_date: Target date (None for current date)
    """
    logger.info("=" * 60)
    logger.info("Starting Weekly Summary Generation")
    logger.info("=" * 60)

    # This is a simplified version - in production, you'd query Notion
    # for papers from the past week and analyze them
    logger.info("Weekly summary generation (placeholder)")
    logger.warning("Full weekly summary requires Notion database query integration")


def monthly_summary_job(target_date: str | None = None) -> None:
    """
    Execute monthly summary generation.

    Args:
        target_date: Target date (None for current date)
    """
    logger.info("=" * 60)
    logger.info("Starting Monthly Summary Generation")
    logger.info("=" * 60)

    # This is a simplified version - in production, you'd query Notion
    # for papers from the past month and analyze them
    logger.info("Monthly summary generation (placeholder)")
    logger.warning("Full monthly summary requires Notion database query integration")


def prioritize_papers(
    ranked_papers,
    all_papers,
    interest_papers,
    top_n
) -> list:
    """
    Prioritize papers for detailed processing.

    Args:
        ranked_papers: List of PaperRanking from papers.cool
        all_papers: List of PaperMetadata from arXiv
        interest_papers: List of PaperMetadata matching interests
        top_n: Number of top papers for detailed reports

    Returns:
        List of dicts with paper and processing flag
    """
    # Create mapping of paper_id to metadata
    paper_map = {p.paper_id: p for p in all_papers}

    # Track papers needing detailed reports
    detailed_ids = set()

    prioritized = []

    # Top N ranked papers
    for rank, ranking in enumerate(ranked_papers[:top_n], 1):
        if ranking.paper_id in paper_map:
            detailed_ids.add(ranking.paper_id)
            prioritized.append({
                "paper": paper_map[ranking.paper_id],
                "rank": rank,
                "needs_detailed_report": True,
                "reason": "top_ranked"
            })

    # Interest-matching papers not in top N
    for paper in interest_papers:
        if paper.paper_id not in detailed_ids:
            detailed_ids.add(paper.paper_id)
            prioritized.append({
                "paper": paper,
                "rank": len(prioritized) + 1,
                "needs_detailed_report": True,
                "reason": "interest_match"
            })

    # Remaining papers (basic info only)
    for ranking in ranked_papers[top_n:]:
        if ranking.paper_id not in detailed_ids and ranking.paper_id in paper_map:
            prioritized.append({
                "paper": paper_map[ranking.paper_id],
                "rank": len(prioritized) + 1,
                "needs_detailed_report": False,
                "reason": "standard"
            })

    return prioritized


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Daily arXiv Paper Collection System"
    )
    parser.add_argument(
        "--mode",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Execution mode"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Target date in YYYY-MM-DD format (for daily mode)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Execute based on mode
    if args.mode == "daily":
        daily_collection_job(args.date)
    elif args.mode == "weekly":
        weekly_summary_job(args.date)
    elif args.mode == "monthly":
        monthly_summary_job(args.date)


if __name__ == "__main__":
    main()
