"""
Notion API client for uploading papers to Notion database.
Handles page creation and block uploads.
"""
from typing import List, Dict, Any
from notion_client import Client as NotionClient
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class NotionAPI:
    """Client for Notion API."""

    def __init__(
        self,
        api_key: str,
        database_id: str,
        parent_page_id: str
    ):
        """
        Initialize Notion client.

        Args:
            api_key: Notion API key
            database_id: Notion database ID
            parent_page_id: Parent page ID for new pages
        """
        self.client = NotionClient(auth=api_key)
        self.database_id = database_id
        self.parent_page_id = parent_page_id

        logger.info("Initialized Notion API client")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def create_page(self, title: str) -> str:
        """
        Create a new page in the Notion database.

        Args:
            title: Page title

        Returns:
            Created page ID
        """
        logger.info(f"Creating Notion page: {title}")

        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        }

        try:
            response = self.client.pages.create(**page_data)
            page_id = response["id"]
            logger.info(f"Created page with ID: {page_id}")
            return page_id

        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def add_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> None:
        """
        Add blocks to a Notion page.

        Notion API limits to 100 blocks per request, so we paginate.

        Args:
            page_id: Page ID to add blocks to
            blocks: List of Notion blocks
        """
        logger.info(f"Adding {len(blocks)} blocks to page {page_id}")

        # Notion API limit: 100 blocks per request
        batch_size = 100

        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i + batch_size]

            logger.debug(f"Uploading batch {i // batch_size + 1} ({len(batch)} blocks)")

            try:
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=batch
                )

            except Exception as e:
                logger.error(f"Failed to upload batch {i // batch_size + 1}: {e}")
                raise

        logger.info(f"Successfully uploaded {len(blocks)} blocks")

    def upload_daily_papers(
        self,
        blocks: List[Dict[str, Any]],
        date: str
    ) -> str:
        """
        Create a new page and upload daily papers.

        Args:
            blocks: List of Notion blocks
            date: Date string for page title

        Returns:
            Created page ID
        """
        # Create page
        page_title = f"Daily arXiv (cs.CL) - {date}"
        page_id = self.create_page(page_title)

        # Upload blocks
        self.add_blocks(page_id, blocks)

        logger.info(f"Successfully uploaded daily papers for {date}")
        return page_id

    def upload_weekly_summary(
        self,
        blocks: List[Dict[str, Any]],
        week_start: str,
        week_end: str
    ) -> str:
        """
        Create a new page and upload weekly summary.

        Args:
            blocks: List of Notion blocks
            week_start: Week start date
            week_end: Week end date

        Returns:
            Created page ID
        """
        # Create page
        page_title = f"Weekly Summary - {week_start} to {week_end}"
        page_id = self.create_page(page_title)

        # Upload blocks
        self.add_blocks(page_id, blocks)

        logger.info(f"Successfully uploaded weekly summary for {week_start} to {week_end}")
        return page_id

    def upload_monthly_summary(
        self,
        blocks: List[Dict[str, Any]],
        month: str,
        year: int
    ) -> str:
        """
        Create a new page and upload monthly summary.

        Args:
            blocks: List of Notion blocks
            month: Month name
            year: Year

        Returns:
            Created page ID
        """
        # Create page
        page_title = f"Monthly Summary - {month} {year}"
        page_id = self.create_page(page_title)

        # Upload blocks
        self.add_blocks(page_id, blocks)

        logger.info(f"Successfully uploaded monthly summary for {month} {year}")
        return page_id

    def test_connection(self) -> bool:
        """
        Test Notion API connection.

        Returns:
            True if connection successful
        """
        try:
            # Try to retrieve the database
            self.client.databases.retrieve(self.database_id)
            logger.info("Notion API connection test successful")
            return True

        except Exception as e:
            logger.error(f"Notion API connection test failed: {e}")
            return False
