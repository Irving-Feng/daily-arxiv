"""
Papers.cool scraper for extracting ranked arXiv paper IDs.
Papers.cool provides ranked papers by readership.

Uses Playwright for JavaScript-based pagination.
"""
import re
import asyncio
from dataclasses import dataclass
from typing import List, Optional
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class PaperRanking:
    """Represents a paper ranking from papers.cool."""
    rank: int
    title: str
    paper_id: str
    authors: List[str]
    abstract: str
    subjects: List[str]
    publish_date: str

    @property
    def arxiv_url(self) -> str:
        """Get arXiv abstract URL."""
        return f"https://arxiv.org/abs/{self.paper_id}"

    @property
    def pdf_url(self) -> str:
        """Get arXiv PDF URL."""
        return f"https://arxiv.org/pdf/{self.paper_id}.pdf"


class PapersCoolScraper:
    """Scraper for papers.cool website using Playwright."""

    def __init__(self, base_url: str = "https://papers.cool", headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self._browser = None
        self._playwright = None

    async def _init_browser(self):
        """Initialize Playwright browser if not already initialized."""
        if self._browser is None:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=self.headless)
            logger.info("Playwright browser initialized")

    async def _close_browser(self):
        """Close Playwright browser."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.info("Playwright browser closed")

    def fetch_ranked_papers(
        self,
        target_date: str,
        category: str = "cs.CL",
        sort: int = 1
    ) -> List[PaperRanking]:
        """
        Fetch ranked papers from papers.cool for a specific date.

        This is a synchronous wrapper that runs the async implementation.

        Args:
            target_date: Target date in YYYY-MM-DD format
            category: arXiv category (default cs.CL)
            sort: Sort parameter (1 for readership ranking)

        Returns:
            List of PaperRanking objects
        """
        return asyncio.run(self._fetch_ranked_papers_async(target_date, category, sort))

    async def _fetch_ranked_papers_async(
        self,
        target_date: str,
        category: str = "cs.CL",
        sort: int = 1
    ) -> List[PaperRanking]:
        """
        Async implementation to fetch all ranked papers from papers.cool.

        Uses Playwright to handle JavaScript-based pagination.

        Args:
            target_date: Target date in YYYY-MM-DD format
            category: arXiv category (default cs.CL)
            sort: Sort parameter (1 for readership ranking)

        Returns:
            List of PaperRanking objects
        """
        await self._init_browser()

        url = f"{self.base_url}/arxiv/{category}?date={target_date}&sort={sort}"
        logger.info(f"Fetching URL with Playwright: {url}")

        try:
            page = await self._browser.new_page()

            # Navigate to the page - use domcontentloaded instead of networkidle for faster load
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            logger.info("Page loaded, waiting for papers to render...")

            # Wait for initial papers to load
            await page.wait_for_selector("div.panel.paper", timeout=30000)
            logger.info("Initial papers loaded")

            all_papers = []
            last_count = 0
            scroll_attempts = 0
            max_scroll_attempts = 50  # Safety limit

            # Scroll to bottom repeatedly to load all papers
            while scroll_attempts < max_scroll_attempts:
                # Get current papers
                content = await page.content()
                papers = self._parse_papers_html(content)
                current_count = len(papers)

                logger.info(f"Scroll attempt {scroll_attempts + 1}: Found {current_count} papers")

                # Check if we got new papers
                if current_count > last_count:
                    last_count = current_count
                    scroll_attempts = 0  # Reset counter since we made progress
                else:
                    scroll_attempts += 1

                # If no new papers for 3 attempts, we're probably done
                if scroll_attempts >= 3:
                    logger.info(f"No new papers for {scroll_attempts} attempts, likely loaded all papers")
                    break

                # Scroll to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                # Wait for new content to load
                await asyncio.sleep(1.5)

            # Get final content
            final_content = await page.content()
            all_papers = self._parse_papers_html(final_content)

            await page.close()

            logger.info(f"Extracted total of {len(all_papers)} papers from papers.cool")
            return all_papers

        except Exception as e:
            logger.error(f"Error fetching papers.cool with Playwright: {e}")
            return []
        finally:
            await self._close_browser()

    def _parse_papers_html(self, html_content: str) -> List[PaperRanking]:
        """
        Parse papers from papers.cool HTML content.

        The HTML structure is:
        <div id="PAPER_ID" class="panel paper" keywords="...">
            <h2 class="title">
                <span class="index">#RANK</span>
                <a class="title-link">TITLE</a>
                <a class="title-pdf" data="PDF_URL">[PDF...]</a>
            </h2>
            <p id="authors-PAPER_ID" class="metainfo authors">Authors...</p>
            <p id="summary-PAPER_ID" class="summary">Abstract...</p>
            <p id="subjects-PAPER_ID" class="metainfo subjects">Subjects...</p>
        </div>

        Args:
            html_content: Raw HTML content from papers.cool

        Returns:
            List of PaperRanking objects
        """
        soup = BeautifulSoup(html_content, 'lxml')
        papers = []

        # Find all paper divs
        paper_divs = soup.find_all('div', class_='panel paper')

        if not paper_divs:
            logger.warning("No papers found in HTML. The date may not have any papers yet.")
            # Check if it shows "Total: 0"
            info_text = soup.find('p', class_='info')
            if info_text:
                logger.info(f"Info text: {info_text.get_text(strip=True)}")
            return []

        logger.debug(f"Found {len(paper_divs)} paper divs in current content")

        for div in paper_divs:
            try:
                # Extract paper ID from div id attribute
                paper_id = div.get('id')
                if not paper_id:
                    logger.warning("Paper div missing id attribute, skipping")
                    continue

                # Extract rank from the index span
                index_span = div.find('span', class_='index')
                if index_span:
                    rank_text = index_span.get_text(strip=True)
                    # Extract number from "#1" format
                    rank_match = re.search(r'#(\d+)', rank_text)
                    if rank_match:
                        rank = int(rank_match.group(1))
                    else:
                        rank = 0
                else:
                    rank = 0

                # Extract title
                title_link = div.find('a', class_='title-link')
                if title_link:
                    title = title_link.get_text(strip=True)
                else:
                    logger.warning(f"Paper {paper_id} missing title, skipping")
                    continue

                # Extract PDF URL
                pdf_link = div.find('a', class_='title-pdf')
                pdf_url = ""
                if pdf_link:
                    pdf_url = pdf_link.get('data', '')

                # Extract authors
                authors_p = div.find('p', class_='metainfo authors')
                authors = []
                if authors_p:
                    author_links = authors_p.find_all('a', class_='author')
                    authors = [a.get_text(strip=True) for a in author_links]

                # Extract abstract
                summary_p = div.find('p', class_='summary')
                abstract = ""
                if summary_p:
                    abstract = summary_p.get_text(strip=True)

                # Extract subjects
                subjects_p = div.find('p', class_='metainfo subjects')
                subjects = []
                if subjects_p:
                    subject_links = subjects_p.find_all('a', href=True)
                    subjects = [a.get_text(strip=True) for a in subject_links]

                # Publish date - use the date from the URL since it's not in the paper div
                publish_date = ""  # Will be set by caller

                paper = PaperRanking(
                    rank=rank,
                    title=title,
                    paper_id=paper_id,
                    authors=authors,
                    abstract=abstract,
                    subjects=subjects,
                    publish_date=publish_date
                )

                papers.append(paper)
                logger.debug(f"Parsed paper #{rank}: {title[:50]}...")

            except Exception as e:
                logger.warning(f"Failed to parse paper div: {e}")
                continue

        return papers
