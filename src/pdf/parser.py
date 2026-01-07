"""
PDF parser for extracting text from arXiv papers.
Uses PyMuPDF (fitz) for text extraction.
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List
from loguru import logger


class PDFParser:
    """Extracts text from PDF files using PyMuPDF."""

    def __init__(self, max_chars: int = 30000):
        """
        Initialize PDF parser.

        Args:
            max_chars: Maximum characters to extract (for LLM context)
        """
        self.max_chars = max_chars
        logger.info(f"Initialized PDF parser (max chars: {max_chars})")

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text
        """
        logger.debug(f"Extracting text from {pdf_path.name}")

        try:
            doc = fitz.open(pdf_path)
            text = ""

            for page_num, page in enumerate(doc):
                # Extract text from page
                page_text = page.get_text()

                text += page_text + "\n\n"

                # Check if we've reached max_chars
                if len(text) >= self.max_chars:
                    text = text[:self.max_chars]
                    logger.debug(
                        f"Reached max_chars at page {page_num + 1}, "
                        f"total pages: {len(doc)}"
                    )
                    break

            doc.close()

            # Clean up whitespace
            text = self._clean_text(text)

            logger.debug(f"Extracted {len(text)} characters")
            return text

        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path.name}: {e}")
            raise

    def extract_text_smart(self, pdf_path: Path) -> str:
        """
        Extract text from PDF with smart section prioritization.
Prioritizes: abstract → introduction → conclusion → methods.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text with smart section ordering
        """
        logger.debug(f"Smart text extraction from {pdf_path.name}")

        try:
            doc = fitz.open(pdf_path)

            # Extract all text first
            all_text = ""
            for page in doc:
                all_text += page.get_text() + "\n\n"

            doc.close()

            # Smart extraction: prioritize sections
            sections = self._extract_sections(all_text)

            # Build prioritized text
            prioritized_text = ""

            # Priority 1: Abstract (if available)
            if "abstract" in sections:
                prioritized_text += sections["abstract"] + "\n\n"

            # Priority 2: Introduction
            if "introduction" in sections:
                prioritized_text += sections["introduction"] + "\n\n"

            # Priority 3: Conclusion
            if "conclusion" in sections:
                prioritized_text += sections["conclusion"] + "\n\n"

            # Priority 4: Methods/Approach
            for key in ["method", "approach", "methodology"]:
                if key in sections:
                    prioritized_text += sections[key] + "\n\n"
                    break

            # If no sections found, use full text
            if not prioritized_text:
                prioritized_text = all_text

            # Truncate to max_chars
            if len(prioritized_text) > self.max_chars:
                prioritized_text = prioritized_text[:self.max_chars]

            # Clean up
            prioritized_text = self._clean_text(prioritized_text)

            logger.debug(f"Smart extraction: {len(prioritized_text)} characters")
            return prioritized_text

        except Exception as e:
            logger.error(f"Failed smart extraction from {pdf_path.name}: {e}")
            # Fall back to basic extraction
            return self.extract_text(pdf_path)

    def chunk_text(self, text: str, chunk_size: int = 8000, overlap: int = 400) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            chunk_size: Size of each chunk
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap

        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = ' '.join(text.split())

        return text.strip()

    @staticmethod
    def _extract_sections(text: str) -> dict:
        """
        Extract common sections from academic paper text.

        Args:
            text: Full paper text

        Returns:
            Dictionary of section names to content
        """
        sections = {}
        text_lower = text.lower()

        # Common section headers (case-insensitive)
        section_patterns = [
            "abstract",
            "introduction",
            "related work",
            "background",
            "method",
            "methodology",
            "approach",
            "experiments",
            "results",
            "discussion",
            "conclusion",
            "limitations",
            "future work"
        ]

        # Simple section extraction
        # This is a basic implementation; could be improved with NLP
        for pattern in section_patterns:
            # Find section header
            idx = text_lower.find(f"\n\n{pattern}\n")
            if idx == -1:
                idx = text_lower.find(f"\n{pattern}\n")

            if idx != -1:
                # Extract section (until next section or end)
                start_idx = idx + len(pattern) + 2

                # Find next section
                end_idx = len(text)
                for next_pattern in section_patterns:
                    if next_pattern == pattern:
                        continue
                    next_idx = text_lower.find(f"\n\n{next_pattern}\n", start_idx)
                    if next_idx != -1 and next_idx < end_idx:
                        end_idx = next_idx

                section_text = text[start_idx:end_idx].strip()
                sections[pattern] = section_text

        return sections
