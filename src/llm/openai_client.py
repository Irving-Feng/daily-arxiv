"""
OpenAI API client for LLM-based paper analysis.
Handles translation and summarization using OpenAI API.
"""
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

from src.llm.prompts import Prompts
from src.arxiv.arxiv_client import PaperMetadata


@dataclass
class DetailedReport:
    """Detailed paper report with 6 sections."""
    background: str
    methods: str
    innovations: str
    results: str
    limitations: str
    applications: str


class OpenAIClient:
    """Client for OpenAI API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        max_tokens: int = 4000,
        temperature: float = 0.3
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            base_url: API base URL
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Response temperature (0-1)
        """
        import httpx

        # Create httpx client without proxy to avoid compatibility issues
        http_client = httpx.Client(timeout=60.0)

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=http_client
        )
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.prompts = Prompts()

        logger.info(f"Initialized OpenAI client with model: {model}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def _generate_completion(self, prompt: str) -> str:
        """
        Generate completion with retry logic.

        Args:
            prompt: Input prompt

        Returns:
            Generated text
        """
        logger.debug(f"Generating completion (model: {self.model})")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        result = response.choices[0].message.content.strip()
        return result

    def translate_title(self, title: str) -> str:
        """
        Translate paper title to Chinese.

        Args:
            title: English title

        Returns:
            Chinese translation
        """
        prompt = self.prompts.title_translation_prompt(title)
        translation = self._generate_completion(prompt)
        logger.debug(f"Translated title: {title[:30]}... → {translation[:30]}...")
        return translation

    def translate_abstract(self, abstract: str) -> str:
        """
        Translate abstract to Chinese.

        Args:
            abstract: English abstract

        Returns:
            Chinese translation
        """
        prompt = self.prompts.abstract_translation_prompt(abstract)
        translation = self._generate_completion(prompt)
        logger.debug(f"Translated abstract ({len(abstract)} chars)")
        return translation

    def generate_detailed_report(
        self,
        title: str,
        abstract: str,
        pdf_text: str
    ) -> Optional[DetailedReport]:
        """
        Generate detailed paper report from PDF text.

        Args:
            title: Paper title
            abstract: Paper abstract
            pdf_text: Extracted text from PDF

        Returns:
            DetailedReport object or None if generation fails
        """
        try:
            prompt = self.prompts.detailed_report_prompt(title, abstract, pdf_text)
            response = self._generate_completion(prompt)

            # Parse response into sections
            report = self._parse_detailed_report(response)
            logger.info(f"Generated detailed report for: {title[:50]}...")
            return report

        except Exception as e:
            logger.error(f"Failed to generate detailed report: {e}")
            return None

    def generate_basic_summary(self, title: str, abstract: str) -> str:
        """
        Generate basic 2-3 sentence summary.

        Args:
            title: Paper title
            abstract: Paper abstract

        Returns:
            Chinese summary (2-3 sentences)
        """
        prompt = self.prompts.basic_summary_prompt(title, abstract)
        summary = self._generate_completion(prompt)
        logger.debug(f"Generated basic summary for: {title[:30]}...")
        return summary

    def generate_weekly_summary(
        self,
        period_start: str,
        period_end: str,
        total_papers: int,
        trending_categories: str,
        top_keywords: str,
        interest_papers_summary: str
    ) -> str:
        """
        Generate weekly summary report.

        Args:
            period_start: Start date
            period_end: End date
            total_papers: Total papers
            trending_categories: Trending categories string
            top_keywords: Top keywords string
            interest_papers_summary: Interest papers summary

        Returns:
            Weekly summary in Chinese
        """
        prompt = self.prompts.weekly_summary_prompt(
            period_start=period_start,
            period_end=period_end,
            total_papers=total_papers,
            trending_categories=trending_categories,
            top_keywords=top_keywords,
            interest_papers_summary=interest_papers_summary
        )

        summary = self._generate_completion(prompt)
        logger.info(f"Generated weekly summary for {period_start} to {period_end}")
        return summary

    def generate_monthly_summary(
        self,
        month: str,
        year: int,
        total_papers: int,
        category_distribution: str,
        outstanding_papers: str
    ) -> str:
        """
        Generate monthly summary report.

        Args:
            month: Month name
            year: Year
            total_papers: Total papers
            category_distribution: Category distribution
            outstanding_papers: Outstanding papers summary

        Returns:
            Monthly summary in Chinese
        """
        prompt = self.prompts.monthly_summary_prompt(
            month=month,
            year=year,
            total_papers=total_papers,
            category_distribution=category_distribution,
            outstanding_papers=outstanding_papers
        )

        summary = self._generate_completion(prompt)
        logger.info(f"Generated monthly summary for {month} {year}")
        return summary

    @staticmethod
    def _parse_detailed_report(response: str) -> DetailedReport:
        """
        Parse LLM response into DetailedReport sections.

        Expected format with section headers:
        **研究背景** ...
        **核心方法** ...
        etc.

        Args:
            response: LLM response text

        Returns:
            DetailedReport object
        """
        # Section markers
        sections = {
            "研究背景": "background",
            "核心方法": "methods",
            "主要创新": "innovations",
            "实验结果": "results",
            "局限性": "limitations",
            "应用价值": "applications"
        }

        # Initialize with empty strings
        parsed = {key: "" for key in sections.values()}

        # Split response by section headers
        current_section = None
        current_content = []

        lines = response.split('\n')
        for line in lines:
            # Check if line is a section header
            found_section = None
            for zh_header, en_key in sections.items():
                if zh_header in line or en_key in line:
                    found_section = en_key
                    break

            if found_section:
                # Save previous section
                if current_section:
                    parsed[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = found_section
                current_content = []
            elif current_section:
                # Add line to current section
                current_content.append(line)

        # Save last section
        if current_section:
            parsed[current_section] = '\n'.join(current_content).strip()

        return DetailedReport(**parsed)
