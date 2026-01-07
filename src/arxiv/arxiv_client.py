"""
arXiv API client for fetching paper metadata.
Uses the arxiv library for querying arXiv API.
"""
import arxiv
from dataclasses import dataclass, field
from typing import List, Optional
from loguru import logger


@dataclass
class PaperMetadata:
    """Metadata for an arXiv paper."""
    paper_id: str
    title: str
    authors: List[str]
    summary: str
    published: str
    categories: List[str]
    pdf_url: str
    arxiv_url: str
    entry_id: str
    match_score: float = 0.0  # For interest matching

    @property
    def primary_category(self) -> str:
        """Get the primary arXiv category."""
        return self.categories[0] if self.categories else ""


class ArxivClient:
    """Client for interacting with arXiv API."""

    def __init__(self, delay_seconds: float = 3.0, max_retries: int = 3):
        """
        Initialize arXiv client.

        Args:
            delay_seconds: Delay between API calls (arXiv recommends 3 seconds)
            max_retries: Maximum number of retry attempts
        """
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=delay_seconds,
            num_retries=max_retries
        )

    def get_papers_by_ids(self, paper_ids: List[str]) -> List[PaperMetadata]:
        """
        Fetch paper metadata by arXiv IDs.

        Args:
            paper_ids: List of arXiv paper IDs (e.g., ["2501.12345", "2312.67890"])

        Returns:
            List of PaperMetadata objects
        """
        logger.info(f"Fetching metadata for {len(paper_ids)} papers from arXiv")

        # Clean paper IDs (remove version numbers if present)
        clean_ids = [self._clean_paper_id(pid) for pid in paper_ids]

        # Create search query
        search = arxiv.Search(id_list=clean_ids)

        # Fetch results
        papers_metadata = []
        try:
            results = list(self.client.results(search))
            logger.info(f"Successfully fetched {len(results)} papers from arXiv")

            for result in results:
                metadata = self._convert_to_metadata(result)
                papers_metadata.append(metadata)

        except Exception as e:
            logger.error(f"Error fetching papers from arXiv: {e}")
            raise

        return papers_metadata

    def get_paper_by_id(self, paper_id: str) -> Optional[PaperMetadata]:
        """
        Fetch a single paper's metadata by ID.

        Args:
            paper_id: arXiv paper ID

        Returns:
            PaperMetadata object or None if not found
        """
        papers = self.get_papers_by_ids([paper_id])
        return papers[0] if papers else None

    def search_papers(
        self,
        query: str,
        max_results: int = 100,
        category: Optional[str] = None
    ) -> List[PaperMetadata]:
        """
        Search for papers by query string.

        Args:
            query: Search query (e.g., "machine learning")
            max_results: Maximum number of results
            category: Filter by arXiv category (e.g., "cs.CL")

        Returns:
            List of PaperMetadata objects
        """
        logger.info(f"Searching arXiv with query: {query}")

        # Build search query
        search_query = f"all:{query}"
        if category:
            search_query += f" AND cat:{category}"

        search = arxiv.Search(
            query=search_query,
            max_results=max_results
        )

        papers_metadata = []
        try:
            results = list(self.client.results(search))
            logger.info(f"Found {len(results)} papers")

            for result in results:
                metadata = self._convert_to_metadata(result)
                papers_metadata.append(metadata)

        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            raise

        return papers_metadata

    @staticmethod
    def _clean_paper_id(paper_id: str) -> str:
        """
        Clean paper ID by removing version numbers.

        Args:
            paper_id: Raw paper ID (e.g., "2501.12345v1")

        Returns:
            Cleaned paper ID (e.g., "2501.12345")
        """
        # Remove version suffix if present
        if 'v' in paper_id:
            # Find the last 'v' that's followed by a number (version marker)
            import re
            match = re.match(r'^(.+?)v\d+$', paper_id)
            if match:
                return match.group(1)
        return paper_id

    @staticmethod
    def _convert_to_metadata(result: arxiv.Result) -> PaperMetadata:
        """
        Convert arxiv.Result to PaperMetadata.

        Args:
            result: arxiv.Result object

        Returns:
            PaperMetadata object
        """
        # Extract paper ID from entry_id
        # entry_id format: http://arxiv.org/abs/2501.12345v1
        paper_id = result.entry_id.split('/')[-1]
        paper_id = ArxivClient._clean_paper_id(paper_id)

        # Format authors
        authors = [str(author.name) for author in result.authors]

        # Format published date
        published = result.published.strftime("%Y-%m-%d %H:%M:%S %Z")

        # Get categories
        categories = list(result.categories)

        return PaperMetadata(
            paper_id=paper_id,
            title=result.title.strip(),
            authors=authors,
            summary=result.summary.strip(),
            published=published,
            categories=categories,
            pdf_url=result.pdf_url,
            arxiv_url=result.entry_id,
            entry_id=result.entry_id
        )
