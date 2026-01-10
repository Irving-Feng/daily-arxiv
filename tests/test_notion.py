#!/usr/bin/env python3
"""
Test script for Notion API connection and functionality.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config import get_settings
from src.notion.client import NotionAPI
from src.notion.blocks import create_heading_block, create_paragraph_block


def test_notion_connection():
    """Test Notion API connection."""
    logger.info("=" * 60)
    logger.info("Testing Notion API Connection")
    logger.info("=" * 60)

    # Load settings
    settings = get_settings()

    # Initialize Notion client
    notion = NotionAPI(
        api_key=settings.notion_api_key,
        database_id=settings.notion_database_id,
        parent_page_id=settings.notion_parent_page_id
    )

    # Test connection
    logger.info("Testing connection to Notion API...")
    if notion.test_connection():
        logger.success("✓ Notion API connection successful!")

        # Try to retrieve database info
        try:
            database = notion.client.databases.retrieve(settings.notion_database_id)
            logger.info(f"✓ Database title: {database['title'][0]['plain_text']}")
            logger.info(f"✓ Database ID: {settings.notion_database_id}")
        except Exception as e:
            logger.error(f"✗ Error accessing database: {e}")
            return False

        return True
    else:
        logger.error("✗ Notion API connection failed!")
        return False


def test_notion_page_creation():
    """Test creating a page in Notion."""
    logger.info("=" * 60)
    logger.info("Testing Notion Page Creation")
    logger.info("=" * 60)

    settings = get_settings()
    notion = NotionAPI(
        api_key=settings.notion_api_key,
        database_id=settings.notion_database_id,
        parent_page_id=settings.notion_parent_page_id
    )

    try:
        # Create a test page
        test_title = "Test Page - Daily arXiv System"
        logger.info(f"Creating test page: {test_title}")

        page_id = notion.create_page(test_title)
        logger.success(f"✓ Test page created successfully!")
        logger.info(f"  Page ID: {page_id}")

        # Add some test blocks
        logger.info("Adding test blocks...")
        test_blocks = [
            create_heading_block("Test Heading", level=2),
            create_paragraph_block("This is a test paragraph created by the Daily arXiv system.")
        ]

        notion.add_blocks(page_id, test_blocks)
        logger.success("✓ Test blocks added successfully!")

        logger.info(f"✓ Check your Notion database for the test page: {test_title}")
        return True

    except Exception as e:
        logger.error(f"✗ Error creating test page: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Notion API")
    parser.add_argument("--create-page", action="store_true", help="Test page creation")
    args = parser.parse_args()

    # Setup logging
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    if args.create_page:
        success = test_notion_page_creation()
    else:
        success = test_notion_connection()

    sys.exit(0 if success else 1)
