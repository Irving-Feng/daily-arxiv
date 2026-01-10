#!/usr/bin/env python3
"""
Test script for arXiv API client.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from src.arxiv.arxiv_client import ArxivClient


# Sample paper IDs for testing (recent cs.CL papers)
SAMPLE_PAPER_IDS = [
    "2501.12345",  # Replace with actual recent paper IDs
    "2501.12346",
    "2501.12347"
]


def test_arxiv_client(paper_ids: list = None):
    """Test arXiv API client."""
    logger.info("=" * 60)
    logger.info("Testing arXiv API Client")
    logger.info("=" * 60)

    # Use sample IDs if none provided
    if paper_ids is None:
        paper_ids = SAMPLE_PAPER_IDS

    logger.info(f"Testing with {len(paper_ids)} paper IDs: {paper_ids}")

    # Initialize client
    client = ArxivClient()

    try:
        # Test fetching papers by IDs
        logger.info("\nFetching papers from arXiv API...")
        papers = client.get_papers_by_ids(paper_ids)

        if not papers:
            logger.warning(f"✗ No papers retrieved")
            logger.info("Note: The sample paper IDs may be outdated. Try with real IDs.")
            return False

        logger.success(f"✓ Successfully retrieved {len(papers)} papers from arXiv")

        # Display paper details
        logger.info("\n" + "=" * 60)
        logger.info("Retrieved Papers:")
        logger.info("=" * 60)

        for i, paper in enumerate(papers, 1):
            logger.info(f"\n{i}. Paper: {paper.paper_id}")
            logger.info(f"   Title: {paper.title}")
            logger.info(f"   Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
            logger.info(f"   Published: {paper.published}")
            logger.info(f"   Categories: {', '.join(paper.categories)}")
            logger.info(f"   Primary Category: {paper.primary_category}")
            logger.info(f"   PDF URL: {paper.pdf_url}")
            logger.info(f"   arXiv URL: {paper.arxiv_url}")
            logger.info(f"   Abstract: {paper.summary[:150]}...")

        logger.info("\n" + "=" * 60)
        logger.info("Validation Checks:")
        logger.info("=" * 60)

        # Check required fields
        all_valid = True
        for paper in papers:
            if not paper.title:
                logger.error(f"✗ Paper {paper.paper_id} missing title")
                all_valid = False
            if not paper.authors:
                logger.error(f"✗ Paper {paper.paper_id} missing authors")
                all_valid = False
            if not paper.summary:
                logger.error(f"✗ Paper {paper.paper_id} missing abstract")
                all_valid = False
            if not paper.pdf_url:
                logger.error(f"✗ Paper {paper.paper_id} missing PDF URL")
                all_valid = False
            if not paper.categories:
                logger.error(f"✗ Paper {paper.paper_id} missing categories")
                all_valid = False

        if all_valid:
            logger.success("✓ All papers have complete metadata")

        return True

    except Exception as e:
        logger.error(f"✗ Error fetching from arXiv: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_arxiv_search():
    """Test arXiv search functionality."""
    logger.info("=" * 60)
    logger.info("Testing arXiv Search")
    logger.info("=" * 60)

    client = ArxivClient()

    try:
        # Search for recent papers
        query = "machine learning"
        logger.info(f"Searching for: {query}")

        papers = client.search_papers(
            query=query,
            max_results=5,
            category="cs.CL"
        )

        logger.success(f"✓ Found {len(papers)} papers")

        logger.info("\nSearch Results:")
        for i, paper in enumerate(papers, 1):
            logger.info(f"{i}. {paper.title}")

        return True

    except Exception as e:
        logger.error(f"✗ Error searching arXiv: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test arXiv API")
    parser.add_argument("--paper-ids", nargs="+", help="Paper IDs to test (e.g., 2501.12345 2501.12346)")
    parser.add_argument("--search", action="store_true", help="Test search functionality")
    args = parser.parse_args()

    # Setup logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    if args.search:
        success = test_arxiv_search()
    else:
        success = test_arxiv_client(args.paper_ids)

    sys.exit(0 if success else 1)
