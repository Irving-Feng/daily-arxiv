# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated system to collect, analyze, and summarize daily arXiv cs.CL papers. The system scrapes ranked papers from papers.cool, fetches metadata from arXiv API, matches papers against user interests, generates Chinese summaries using OpenAI API, and publishes formatted reports to Notion.

**Key Data Flow**: papers.cool scraper → arXiv API → keyword matching → PDF download/parsing → OpenAI LLM processing → Notion upload

## Development Commands

### Running the Application

```bash
# Daily collection (for yesterday)
python main.py --mode daily

# Daily collection for specific date
python main.py --mode daily --date 2026-01-05

# Weekly summary
python main.py --mode weekly

# Monthly summary
python main.py --mode monthly
```

### Testing

All test files are in the `tests/` directory. Run tests from the project root:

```bash
# Test individual components
python tests/test_notion.py                          # Test Notion API connection
python tests/test_papers_cool.py                    # Test papers.cool scraper
python tests/test_arxiv.py --search                 # Test arXiv API client
python tests/test_llm.py --test all                 # Test all LLM functions (slow)
python tests/test_llm.py --test summary             # Test basic summary (faster)

# Run all automated tests
./run_all_tests.sh
```

**Important**: The test script references test files without the `tests/` prefix, so tests must be run from the project root directory.

### Installing Dependencies

```bash
pip install -r requirements.txt
playwright install chromium  # Required for papers.cool scraper
```

## Architecture

### Module Structure

```
src/
├── scrapers/           # papers.cool scraper (Playwright-based)
├── arxiv/              # arXiv API client
├── pdf/                # PDF download and text extraction
├── llm/                # OpenAI integration (translation, reports)
├── notion/             # Notion API client and formatting
├── analysis/           # Keyword matching and trend analysis
└── utils/              # Logging, date utilities, rate limiting
```

### Key Components

**PapersCoolScraper** (`src/scrapers/papers_cool_scraper.py`)
- Uses Playwright for headless browser automation
- Handles JavaScript-based pagination on papers.cool
- Returns ranked papers with metadata (rank, title, paper_id, authors, subjects)

**ArxivClient** (`src/arxiv/arxiv_client.py`)
- Queries arXiv API for full paper metadata
- Implements rate limiting (3-second delays between requests)
- Returns `PaperMetadata` objects

**KeywordMatcher** (`src/analysis/keyword_matcher.py`)
- Matches papers against user interests (configurable via `USER_INTERESTS`)
- Searches in title, abstract, and author fields
- Returns list of matching papers

**PDFDownloader** & **PDFParser** (`src/pdf/`)
- Downloads PDFs with size limits (configurable via `MAX_PDF_SIZE_MB`)
- Extracts text using PyMuPDF (fitz)
- Smart text extraction with fallback strategies

**OpenAIClient** (`src/llm/openai_client.py`)
- Translates titles and abstracts to Chinese
- Generates detailed 6-section reports (background, methods, innovations, results, limitations, applications)
- Generates basic summaries for papers without PDFs
- Uses tenacity for automatic retry on failures

**NotionAPI** & **NotionFormatter** (`src/notion/`)
- Creates pages in Notion database
- Formats papers with numbered lists, Chinese abstracts, collapsible detailed sections
- Uses retry logic for robustness

### Processing Pipeline

The main pipeline in `main.py:daily_collection_job()` orchestrates these steps:

1. **Scrape**: Fetch ranked papers from papers.cool for target date
2. **Enrich**: Retrieve full metadata from arXiv API
3. **Match**: Find papers matching user interests
4. **Prioritize**: Select top N papers + interest-matching papers for detailed analysis
5. **Process**: Generate Chinese translations and detailed reports (with PDF extraction)
6. **Upload**: Create formatted Notion page with all papers

**Prioritization Logic**:
- Top 15 papers (configurable via `TOP_PAPERS_COUNT`) get detailed reports
- Interest-matching papers get detailed reports even if not in top 15
- Remaining papers get basic summary only

## Configuration

### Environment Variables

All configuration is managed via `config.py` using pydantic-settings. Required variables:

**OpenAI**:
- `OPENAI_API_KEY`: API key
- `OPENAI_BASE_URL`: API endpoint (default: https://api.openai.com/v1)
- `OPENAI_MODEL`: Model name (default: gpt-4o-mini)
- `OPENAI_MAX_TOKENS`: Response token limit (default: 4000)
- `OPENAI_TEMPERATURE`: Temperature (default: 0.3)

**Notion**:
- `NOTION_API_KEY`: Integration token
- `NOTION_DATABASE_ID`: Target database ID
- `NOTION_PARENT_PAGE_ID`: Parent page for new pages

**Application**:
- `ARXIV_CATEGORY`: arXiv category (default: cs.CL)
- `USER_INTERESTS`: Comma-separated interests for matching
- `TOP_PAPERS_COUNT`: Number of top papers for detailed reports (default: 15)
- `TIMEZONE`: Timezone for date calculations (default: Asia/Shanghai)
- `MAX_PDF_SIZE_MB`: Maximum PDF download size (default: 50)

### Local vs GitHub Actions

- **Local development**: Uses `.env` file
- **GitHub Actions**: Uses repository secrets (configure in Settings → Secrets)
- Both use the same `config.py` with pydantic-settings auto-loading

## GitHub Actions

### Workflow Files

- `.github/workflows/daily-arxiv.yml`: Runs daily at 6:00 AM Beijing time
- `.github/workflows/weekly-summary.yml`: Runs Sundays at 7:00 AM Beijing time
- `.github/workflows/monthly-summary.yml`: Runs last day of month at 8:00 AM Beijing time

All workflows support manual triggering with mode and date parameters.

### Workflow Structure

Each workflow:
1. Checks out code
2. Sets up Python 3.11
3. Installs dependencies (including Playwright browser)
4. Loads environment from GitHub Secrets
5. Runs `main.py` with appropriate mode
6. Has 60-minute timeout

### Important Notes

- The workflows install Playwright browser automatically: `playwright install chromium`
- All secrets must be configured in GitHub repository settings before running
- Weekly and monthly summary features are placeholder implementations (require Notion database query integration)

## Common Issues and Solutions

**Playwright browser not found**: Run `playwright install chromium` after installing dependencies

**papers.cool scraper fails**: The website structure may have changed; check if HTML parsing logic needs updates

**arXiv API rate limiting**: Built-in 3-second delays between requests; if still failing, may need to increase delays

**PDF parsing fails**: Falls back to basic summary; check if PDF URL is accessible and size is within limits

**Notion API errors**: Verify database ID is correct, integration has proper permissions, and parent page exists

**OpenAI API quota issues**: Check API quota/billing; consider using smaller `MAX_TOKENS` or faster model

**Date/time issues**: All date calculations use `TIMEZONE` setting (default: Asia/Shanghai); ensure this matches your needs

## Testing Strategy

When making changes:

1. Run relevant component test first (e.g., `python tests/test_notion.py` for Notion changes)
2. Run full automated test suite: `./run_all_tests.sh`
3. If tests pass, run end-to-end test with a specific date: `python main.py --mode daily --date 2026-01-05`
4. Verify output in Notion database
5. Only then deploy to GitHub Actions

**Test Date Note**: Use dates when papers.cool has data (avoid weekends/holidays for initial testing)