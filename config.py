"""
Configuration management for Daily arXiv Paper Collection System.
Uses pydantic-settings for type-safe configuration loading.
"""
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")
    openai_max_tokens: int = Field(default=4000, description="Max tokens for OpenAI responses")
    openai_temperature: float = Field(default=0.3, description="Temperature for OpenAI responses")

    # Notion Configuration
    notion_api_key: str = Field(..., description="Notion API key")
    notion_database_id: str = Field(..., description="Notion database ID")
    notion_parent_page_id: str = Field(..., description="Notion parent page ID")

    # Application Configuration
    arxiv_category: str = Field(default="cs.CL", description="arXiv category to fetch")
    user_interests: str = Field(
        default="agents,agentic memory,reinforcement learning,reasoning",
        description="Comma-separated list of user interests"
    )
    top_papers_count: int = Field(default=15, description="Number of top papers for detailed analysis")
    timezone: str = Field(default="Asia/Shanghai", description="Timezone for scheduling")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=30, description="API rate limit")

    # PDF Processing
    max_pdf_size_mb: int = Field(default=50, description="Maximum PDF size in MB")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def interests_list(self) -> List[str]:
        """Parse user interests into a list."""
        return [interest.strip() for interest in self.user_interests.split(",")]


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    Loads from environment variables on first call.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
