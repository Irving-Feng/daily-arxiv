#!/usr/bin/env python3
"""
Test script for papers.cool scraper.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.scrapers.papers_cool_scraper import PapersCoolScraper


def test_papers_cool_scraper(date: str = None):
    """Test papers.cool scraper for a specific date."""
    logger.info("=" * 60)
    logger.info("Testing papers.cool Scraper")
    logger.info("=" * 60)

    # Use a default date if none provided (recent date with papers)
    if date is None:
        date = "2024-12-20"  # A date we know has papers

    logger.info(f"Fetching papers for date: {date}")

    # Initialize scraper
    scraper = PapersCoolScraper()

    try:
        # Fetch ranked papers
        papers = scraper.fetch_ranked_papers(
            target_date=date,
            category="cs.CL",
            sort=1
        )

        if not papers:
            logger.warning(f"✗ No papers found for {date}")
            logger.info("Try a different date (papers.cool may not have data for the specified date)")
            return False

        logger.success(f"✓ Successfully retrieved {len(papers)} papers from papers.cool")

        # Display first few papers
        logger.info("\n" + "=" * 60)
        logger.info("Top 5 Papers (by rank):")
        logger.info("=" * 60)

        for i, paper in enumerate(papers[:5], 1):
            logger.info(f"\n{i}. Rank #{paper.rank}")
            logger.info(f"   Title: {paper.title}")
            logger.info(f"   Paper ID: {paper.paper_id}")
            logger.info(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
            logger.info(f"   Abstract: {paper.abstract[:100]}...")
            logger.info(f"   Subjects: {', '.join(paper.subjects)}")
            logger.info(f"   PDF URL: {paper.pdf_url}")
            logger.info(f"   arXiv URL: {paper.arxiv_url}")

        logger.info("\n" + "=" * 60)
        logger.info("Validation Checks:")
        logger.info("=" * 60)

        # Check sorting
        ranks = [p.rank for p in papers]
        if ranks == sorted(ranks):
            logger.success("✓ Papers are correctly sorted by rank")
        else:
            logger.error("✗ Papers are NOT correctly sorted by rank")
            return False

        # Check required fields
        all_valid = True
        for paper in papers:
            if not paper.paper_id:
                logger.error(f"✗ Paper #{paper.rank} missing paper_id")
                all_valid = False
            if not paper.title:
                logger.error(f"✗ Paper #{paper.rank} missing title")
                all_valid = False
            if not paper.pdf_url:
                logger.error(f"✗ Paper #{paper.rank} missing pdf_url")
                all_valid = False

        if all_valid:
            logger.success("✓ All papers have required fields (paper_id, title, pdf_url)")

        return True

    except Exception as e:
        logger.error(f"✗ Error scraping papers.cool: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test papers.cool scraper")
    parser.add_argument("--date", type=str, help="Date in YYYY-MM-DD format (default: 2024-12-20)")
    args = parser.parse_args()

    # Setup logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    success = test_papers_cool_scraper(args.date)
    sys.exit(0 if success else 1)
