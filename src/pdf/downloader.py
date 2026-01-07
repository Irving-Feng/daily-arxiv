"""
PDF downloader for arXiv papers.
Downloads PDF files with error handling and size limits.
"""
import os
import requests
from pathlib import Path
from typing import Optional
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class PDFDownloader:
    """Downloads PDF files from arXiv."""

    def __init__(self, download_dir: str = "data/papers", max_size_mb: int = 50):
        """
        Initialize PDF downloader.

        Args:
            download_dir: Directory to save PDFs
            max_size_mb: Maximum PDF size in MB
        """
        self.download_dir = Path(download_dir)
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024

        # Create download directory if it doesn't exist
        self.download_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized PDF downloader (max size: {max_size_mb}MB)")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.Timeout))
    )
    def download_paper(self, pdf_url: str, paper_id: str) -> Optional[Path]:
        """
        Download a PDF file.

        Args:
            pdf_url: URL to PDF
            paper_id: arXiv paper ID (for filename)

        Returns:
            Path to downloaded file or None if failed
        """
        logger.debug(f"Downloading PDF for {paper_id}")

        try:
            # Stream download to check file size first
            response = requests.get(pdf_url, stream=True, timeout=30)
            response.raise_for_status()

            # Check content length
            content_length = response.headers.get('content-length')
            if content_length:
                content_length = int(content_length)
                if content_length > self.max_size_bytes:
                    logger.warning(
                        f"PDF too large: {content_length / 1024 / 1024:.2f}MB "
                        f"(max: {self.max_size_mb}MB)"
                    )
                    return None

            # Download to file
            pdf_path = self.download_dir / f"{paper_id}.pdf"

            with open(pdf_path, 'wb') as f:
                # Download in chunks
                chunk_size = 8192
                downloaded = 0

                for chunk in response.iter_content(chunk_size=chunk_size):
                    # Check size limit during download
                    downloaded += len(chunk)
                    if downloaded > self.max_size_bytes:
                        logger.warning(f"PDF size exceeded limit during download")
                        # Delete partial file
                        pdf_path.unlink(missing_ok=True)
                        return None

                    f.write(chunk)

            file_size = pdf_path.stat().st_size / 1024 / 1024
            logger.info(f"Downloaded {paper_id}: {file_size:.2f}MB")

            return pdf_path

        except Exception as e:
            logger.error(f"Failed to download {paper_id}: {e}")
            return None

    def cleanup(self, paper_id: str) -> None:
        """
        Delete a downloaded PDF file.

        Args:
            paper_id: arXiv paper ID
        """
        pdf_path = self.download_dir / f"{paper_id}.pdf"

        if pdf_path.exists():
            pdf_path.unlink()
            logger.debug(f"Deleted PDF: {paper_id}")

    def cleanup_all(self) -> None:
        """Delete all downloaded PDF files."""
        for pdf_file in self.download_dir.glob("*.pdf"):
            pdf_file.unlink()

        logger.info("Deleted all downloaded PDFs")
