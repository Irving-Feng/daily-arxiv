#!/usr/bin/env python3
"""
Test script for LLM (OpenAI) report generation.
Tests with real arXiv papers by fetching metadata and PDFs.
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from config import get_settings
from src.arxiv.arxiv_client import ArxivClient
from src.pdf.downloader import PDFDownloader
from src.pdf.parser import PDFParser
from src.llm.openai_client import OpenAIClient


# Default paper ID for testing (a well-known ML paper)
DEFAULT_PAPER_ID = "1706.03762"  # "Attention Is All You Need"


def test_openai_connection():
    """Test OpenAI API connection."""
    logger.info("=" * 60)
    logger.info("Testing OpenAI API Connection")
    logger.info("=" * 60)

    settings = get_settings()

    logger.info(f"API Base URL: {settings.openai_base_url}")
    logger.info(f"Model: {settings.openai_model}")

    client = OpenAIClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        max_tokens=settings.openai_max_tokens,
        temperature=settings.openai_temperature
    )

    try:
        # Simple test completion
        logger.info("\nSending test request to OpenAI API...")
        response = client._generate_completion("Say 'Hello, OpenAI API is working!' in Chinese.")

        logger.success("✓ OpenAI API connection successful!")
        logger.info(f"Response: {response}")
        return True

    except Exception as e:
        logger.error(f"✗ OpenAI API connection failed: {e}")
        return False


def test_full_pipeline(paper_id: str):
    """Test the full LLM pipeline with a real arXiv paper."""
    logger.info("=" * 60)
    logger.info(f"Testing Full LLM Pipeline with arXiv Paper: {paper_id}")
    logger.info("=" * 60)

    settings = get_settings()

    # Initialize clients
    arxiv_client = ArxivClient()
    pdf_downloader = PDFDownloader(max_size_mb=settings.max_pdf_size_mb)
    pdf_parser = PDFParser()
    llm_client = OpenAIClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model,
        max_tokens=settings.openai_max_tokens
    )

    try:
        # Step 1: Fetch paper metadata from arXiv
        logger.info(f"\n[Step 1/5] Fetching paper metadata from arXiv...")
        paper = arxiv_client.get_paper_by_id(paper_id)

        if not paper:
            logger.error(f"✗ Paper {paper_id} not found on arXiv")
            return False

        logger.success(f"✓ Found paper: {paper.title}")
        logger.info(f"  Authors: {', '.join(paper.authors[:3])}{'...' if len(paper.authors) > 3 else ''}")
        logger.info(f"  Published: {paper.published}")
        logger.info(f"  Categories: {', '.join(paper.categories)}")

        # Step 2: Download PDF
        logger.info(f"\n[Step 2/5] Downloading PDF from {paper.pdf_url}...")
        pdf_path = pdf_downloader.download_paper(paper.pdf_url, paper.paper_id)

        if not pdf_path:
            logger.error(f"✗ Failed to download PDF")
            logger.info("  Will test with abstract only...")
            pdf_text = None
        else:
            logger.success(f"✓ PDF downloaded: {pdf_path}")
            file_size_mb = pdf_path.stat().st_size / 1024 / 1024
            logger.info(f"  File size: {file_size_mb:.2f} MB")

        # Step 3: Parse PDF to extract text
        pdf_text = None
        if pdf_path:
            logger.info(f"\n[Step 3/5] Extracting text from PDF...")
            try:
                pdf_text = pdf_parser.extract_text_smart(pdf_path)
                logger.success(f"✓ Extracted {len(pdf_text)} characters from PDF")
                logger.info(f"  Text preview: {pdf_text[:200]}...")
            finally:
                # Cleanup PDF
                pdf_downloader.cleanup(paper.paper_id)

        # Step 4: Test title translation
        logger.info(f"\n[Step 4/5] Testing Title Translation...")
        chinese_title = llm_client.translate_title(paper.title)
        logger.success("✓ Title translation successful!")
        logger.info(f"  Original: {paper.title}")
        logger.info(f"  Chinese:  {chinese_title}")

        # Step 5: Test abstract translation
        logger.info(f"\n[Step 5/5] Testing Abstract Translation...")
        chinese_abstract = llm_client.translate_abstract(paper.summary)
        logger.success("✓ Abstract translation successful!")
        logger.info(f"  Chinese abstract: {chinese_abstract}...")

        # Step 6: Test detailed report (if PDF was downloaded)
        if pdf_text:
            logger.info(f"\n[Bonus] Testing Detailed Report Generation...")
            logger.info("  This may take 30-60 seconds...")

            detailed_report = llm_client.generate_detailed_report(
                title=paper.title,
                abstract=paper.summary,
                pdf_text=pdf_text
            )

            if detailed_report:
                logger.success("✓ Detailed report generation successful!")
                logger.info("\n  ========== Generated Report (Full Content) ==========")
                logger.info(f"\n【1. 研究背景】\n{detailed_report.background}\n")
                logger.info(f"【2. 核心方法】\n{detailed_report.methods}\n")
                logger.info(f"【3. 主要创新】\n{detailed_report.innovations}\n")
                logger.info(f"【4. 实验结果】\n{detailed_report.results}\n")
                logger.info(f"【5. 局限性】\n{detailed_report.limitations if detailed_report.limitations else 'N/A'}\n")
                logger.info(f"【6. 应用价值】\n{detailed_report.applications}")
                logger.info("\n  ================================================")
            else:
                logger.warning("✗ Detailed report generation returned None")
        else:
            logger.info("\n[Bonus] Skipping detailed report (no PDF available)")

        logger.info("\n" + "=" * 60)
        logger.success("✓ Full LLM Pipeline Test Completed Successfully!")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"✗ Full pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_summary(paper_id: str):
    """Test basic summary generation."""
    logger.info("=" * 60)
    logger.info(f"Testing Basic Summary Generation for {paper_id}")
    logger.info("=" * 60)

    settings = get_settings()
    arxiv_client = ArxivClient()
    llm_client = OpenAIClient(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.openai_model
    )

    try:
        # Fetch paper
        paper = arxiv_client.get_paper_by_id(paper_id)
        if not paper:
            logger.error(f"✗ Paper {paper_id} not found")
            return False

        logger.info(f"Paper: {paper.title}")

        # Generate summary
        summary = llm_client.generate_basic_summary(paper.title, paper.summary)

        logger.success("✓ Basic summary generation successful!")
        logger.info(f"Summary: {summary}")

        return True

    except Exception as e:
        logger.error(f"✗ Basic summary test failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test OpenAI/LLM API with real arXiv papers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with default paper (Attention Is All You Need)
  python test_llm.py

  # Test with specific paper ID
  python test_llm.py --paper-id 2301.07041

  # Test connection only
  python test_llm.py --test connection

  # Test basic summary only
  python test_llm.py --test summary --paper-id 2301.07041
        """
    )

    parser.add_argument("--paper-id", type=str, default=DEFAULT_PAPER_ID,
                       help=f"arXiv paper ID (default: {DEFAULT_PAPER_ID})")
    parser.add_argument("--test", choices=["connection", "full", "summary"],
                       default="full", help="Which test to run (default: full)")
    args = parser.parse_args()

    # Setup logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    results = []

    if args.test == "connection":
        success = test_openai_connection()
        sys.exit(0 if success else 1)

    elif args.test == "full":
        success = test_full_pipeline(args.paper_id)
        sys.exit(0 if success else 1)

    elif args.test == "summary":
        success = test_basic_summary(args.paper_id)
        sys.exit(0 if success else 1)
