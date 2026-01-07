# Daily arXiv Paper Collection System

An automated system to collect, analyze, and summarize daily arXiv cs.CL papers with intelligent filtering based on user interests and automated reporting to Notion.

## Features

- **Automated Collection**: Fetches ranked papers from papers.cool daily at 6:00 AM Beijing time
- **Intelligent Filtering**: Matches papers against user interests (agents, agentic memory, reinforcement learning, reasoning)
- **LLM Analysis**: Uses OpenAI API to generate Chinese summaries and detailed reports
- **Notion Integration**: Automatically publishes formatted reports to Notion with:
  - Numbered paper lists with PDF links
  - Chinese abstracts
  - Collapsible detailed analysis sections
- **Weekly/Monthly Summaries**: Generates trend analysis and outstanding paper highlights
- **GitHub Actions**: Fully automated execution via GitHub Actions workflows

## Project Structure

```
daily-arxiv/
├── .github/workflows/       # GitHub Actions workflows
├── config.py                # Configuration management
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── src/
│   ├── scrapers/           # papers.cool scraper
│   ├── arxiv/              # arXiv API client
│   ├── pdf/                # PDF download and parsing
│   ├── llm/                # OpenAI integration
│   ├── notion/             # Notion API client
│   ├── analysis/           # Interest matching and summarization
│   └── utils/              # Logging, date utilities, rate limiting
├── data/                   # Runtime data (PDFs, cache)
└── logs/                   # Application logs
```

## Installation

### Prerequisites

- Python 3.11+
- OpenAI API key
- Notion API key and database ID

### Setup

1. **Clone the repository**:
   ```bash
   cd /bigdata/khfeng/project/claude-code/daily-arxiv
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your credentials:
   ```bash
   # OpenAI Configuration
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_MAX_TOKENS=4000
   OPENAI_TEMPERATURE=0.3

   # Notion Configuration
   NOTION_API_KEY=your-notion-api-key
   NOTION_DATABASE_ID=your-database-id
   NOTION_PARENT_PAGE_ID=your-parent-page-id

   # Application
   ARXIV_CATEGORY=cs.CL
   USER_INTERESTS=agents,agentic memory,reinforcement learning,reasoning
   TOP_PAPERS_COUNT=15
   TIMEZONE=Asia/Shanghai
   ```

## Usage

### Local Execution

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

### GitHub Actions Setup

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/daily-arxiv.git
   git push -u origin main
   ```

2. **Configure GitHub Secrets**:
   Go to **Settings** → **Secrets and variables** → **Actions** and add:
   - `OPENAI_API_KEY`
   - `OPENAI_BASE_URL`
   - `OPENAI_MODEL`
   - `OPENAI_MAX_TOKENS`
   - `OPENAI_TEMPERATURE`
   - `NOTION_API_KEY`
   - `NOTION_DATABASE_ID`
   - `NOTION_PARENT_PAGE_ID`

3. **Enable Workflows**:
   - Go to **Actions** tab
   - GitHub will detect the workflows automatically
   - Workflows will run based on cron schedule

### Manual Workflow Trigger

1. Go to **Actions** tab
2. Select a workflow (e.g., "Daily arXiv Paper Collection")
3. Click **Run workflow**
4. Select mode and optionally specify target date
5. Click **Run workflow**

## Configuration

### User Interests

Edit `USER_INTERESTS` in `.env` or GitHub Secrets:
```bash
USER_INTERESTS=agents,agentic memory,reinforcement learning,reasoning,multi-agent systems
```

### Scheduling

The system uses three GitHub Actions workflows:
- **Daily**: 6:00 AM Beijing time (10:00 PM UTC previous day)
- **Weekly**: Sundays at 7:00 AM Beijing time
- **Monthly**: Last day of month at 8:00 AM Beijing time

### Processing Options

- `TOP_PAPERS_COUNT`: Number of top papers for detailed reports (default: 15)
- `MAX_PDF_SIZE_MB`: Maximum PDF size to download (default: 50MB)
- `TIMEZONE`: Timezone for date calculations (default: Asia/Shanghai)

## Output Format

Papers are published to Notion with the following structure:

```
# Daily arXiv (cs.CL) - 2026-01-05

1. Paper Title (with PDF link)
Authors: Name1, Name2, Name3
Chinese abstract text
📊 详细分析 (collapsible section)
   研究背景
   核心方法
   主要创新
   实验结果
   局限性
   应用价值

2. Next Paper Title
...
```

## Architecture

### Data Flow

```
GitHub Actions (cron trigger)
  ↓
papers.cool Scraper → Extract rankings & paper IDs
  ↓
arXiv API → Fetch full metadata
  ↓
Keyword Matcher → Find interest matches
  ↓
Prioritize → Top 15 + interest matches
  ↓
PDF Download & Parse → Extract text
  ↓
LLM Processing → Chinese translation + detailed reports
  ↓
Notion Upload → Formatted blocks with toggle sections
```

### Components

- **PapersCoolScraper**: Parses papers.cool to extract ranked paper IDs
- **ArxivClient**: Queries arXiv API for full paper metadata
- **KeywordMatcher**: Matches papers against user interests
- **PDFDownloader**: Downloads PDFs with size limits
- **PDFParser**: Extracts text using PyMuPDF
- **OpenAIClient**: Translates and generates reports
- **NotionAPI**: Uploads formatted blocks to Notion
- **TrendAnalyzer**: Generates weekly/monthly summaries

## Troubleshooting

### Workflow Fails

1. Check **Actions** tab → Click on failed run → View logs
2. Download log artifacts if available
3. Common issues:
   - **Missing dependencies**: Check requirements.txt
   - **API rate limits**: Wait and retry
   - **Wrong API keys**: Verify GitHub Secrets
   - **Timeout**: Increase `timeout-minutes` in workflow

### Papers Not Appearing

- Verify Notion database ID and parent page ID
- Check Notion API integration has proper permissions
- Ensure Notion database schema includes "title" property

### LLM Errors

- Check OpenAI API key and base URL
- Verify model name (gpt-4o-mini)
- Check API quota/billing

## Development

### Adding New Features

1. **New data source**: Extend `PapersCoolScraper` or create new scraper
2. **New analysis**: Add methods to `TrendAnalyzer`
3. **New output format**: Extend `NotionFormatter`
4. **Custom prompts**: Add prompts to `Prompts` class

### Testing

The project includes comprehensive test scripts for each major component. Run these tests before deploying to GitHub Actions to ensure everything is configured correctly.

#### 1. Test Notion API Connection

Verify that your Notion API credentials are correct and the system can create pages:

```bash
# Test basic connection
python test_notion.py

# Test page creation (creates a test page in your Notion database)
python test_notion.py --create-page
```

**Expected Output:**
```
✓ Notion API connection successful!
✓ Database title: Your Database Name
✓ Database ID: 2e0bbaccb16f808f88c8f46ac458500c
```

**Common Issues:**
- If connection fails: Verify `NOTION_API_KEY` in `.env`
- If database access fails: Check `NOTION_DATABASE_ID` is correct
- If page creation fails: Ensure your Notion integration has "Insert content" permission

#### 2. Test papers.cool Scraper

Verify that the scraper can extract and rank papers from papers.cool:

```bash
# Test with default date (2026-01-05)
python test_papers_cool.py

# Test with specific date
python test_papers_cool.py --date 2026-01-05
```

**Expected Output:**
```
✓ Successfully retrieved 50 papers from papers.cool

Top 5 Papers (by rank):
1. Rank #1
   Title: [Paper Title]
   Paper ID: 2501.xxxxx
   Authors: Author1, Author2, Author3
   Subjects: cs.CL, cs.AI

✓ Papers are correctly sorted by rank
✓ All papers have required fields (paper_id, title, pdf_url)
```

**Common Issues:**
- No papers found: Try a different date (papers.cool may not have data for weekends/holidays)
- Parsing errors: The website structure may have changed

#### 3. Test arXiv API Client

Verify that the arXiv API client can fetch paper metadata:

```bash
# Test with sample paper IDs
python test_arxiv.py --paper-ids 2501.12345 2501.12346

# Test search functionality
python test_arxiv.py --search
```

**Expected Output:**
```
✓ Successfully retrieved 2 papers from arXiv

Retrieved Papers:
1. Paper: 2501.12345
   Title: [Paper Title]
   Authors: Author1, Author2, Author3
   Published: 2025-01-01 00:00:00 UTC
   Categories: cs.CL, cs.AI
   PDF URL: https://arxiv.org/pdf/2501.12345.pdf

✓ All papers have complete metadata
```

**Common Issues:**
- Invalid paper IDs: Use real arXiv IDs (format: YYYY.NNNNN)
- Rate limiting: The client includes a 3-second delay between requests

#### 4. Test LLM Report Generation

Verify that OpenAI API can generate Chinese translations and reports:

```bash
# Test all components (connection, translation, reports)
python test_llm.py --test all

# Test specific components
python test_llm.py --test connection    # Test API connection only
python test_llm.py --test title         # Test title translation
python test_llm.py --test abstract      # Test abstract translation
python test_llm.py --test detailed      # Test full detailed report (slower)
python test_llm.py --test summary       # Test basic summary
```

**Expected Output:**
```
✓ OpenAI API connection successful!
Response: 你好，OpenAI API 正在工作！

✓ Title translation successful!
Chinese Title: 注意力就是你所需要的全部

✓ Abstract translation successful!
Chinese Abstract: 主导的序列转导模型基于复杂的循环或卷积神经网络...

✓ Detailed report generation successful!
Generated Report Sections:
1. 研究背景: 循环神经网络、长短期记忆...
2. 核心方法: 我们提出了一个新的简单网络架构...
3. 主要创新: 基于注意力机制...
4. 实验结果: 在两个机器翻译任务上的实验表明...
5. 局限性: 模型可能对长序列处理仍有改进空间...
6. 应用价值: 该架构在机器翻译、文本摘要等领域...

Test Summary:
Connection: ✓ PASS
Title Translation: ✓ PASS
Abstract Translation: ✓ PASS
Detailed Report: ✓ PASS
Basic Summary: ✓ PASS
```

**Common Issues:**
- Connection fails: Check `OPENAI_API_KEY` and `OPENAI_BASE_URL` in `.env`
- Rate limit errors: Wait a few minutes and retry
- Slow responses: Report generation takes 30-60 seconds per paper (normal)

#### 5. Full End-to-End Test

Test the complete daily collection pipeline:

```bash
# Run for a specific date (recommended for testing)
python main.py --mode daily --date 2026-01-05
```

**What to Expect:**
1. Fetches ranked papers from papers.cool
2. Retrieves full metadata from arXiv
3. Matches papers against your interests
4. Downloads PDFs for top 15 + interest-matching papers
5. Generates Chinese translations and detailed reports
6. Creates a new page in your Notion database

**Estimated Time:** 10-20 minutes (depending on number of papers)

#### Quick Test Checklist

Before deploying to GitHub Actions, run this quick test sequence:

```bash
# 1. Install dependencies (if not already done)
pip install -r requirements.txt

# 2. Verify configuration
cat .env

# 3. Test all APIs
python test_notion.py                    # ~5 seconds
python test_papers_cool.py              # ~10 seconds
python test_arxiv.py --search           # ~15 seconds
python test_llm.py --test all           # ~2-3 minutes

# 4. Run full pipeline with small dataset
python main.py --mode daily --date 2026-01-05   # ~10-20 minutes

# 5. Verify Notion output
# Check your Notion database for the created page
```

#### Automated Testing Script

For convenience, you can create a test script that runs all tests:

```bash
#!/bin/bash
# run_all_tests.sh

echo "Running all tests..."
echo "================================"

echo "1. Testing Notion API..."
python test_notion.py
if [ $? -ne 0 ]; then
    echo "✗ Notion test failed!"
    exit 1
fi

echo "2. Testing papers.cool scraper..."
python test_papers_cool.py
if [ $? -ne 0 ]; then
    echo "✗ papers.cool test failed!"
    exit 1
fi

echo "3. Testing arXiv API..."
python test_arxiv.py --search
if [ $? -ne 0 ]; then
    echo "✗ arXiv test failed!"
    exit 1
fi

echo "4. Testing LLM generation..."
python test_llm.py --test summary
if [ $? -ne 0 ]; then
    echo "✗ LLM test failed!"
    exit 1
fi

echo "================================"
echo "All tests passed! ✓"
```

Make it executable and run:
```bash
chmod +x run_all_tests.sh
./run_all_tests.sh
```

## License

MIT License - feel free to use and modify for your needs.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [papers.cool](https://papers.cool) for ranked arXiv papers
- [arXiv](https://arxiv.org) for open access papers
- [OpenAI](https://openai.com) for LLM capabilities
- [Notion](https://notion.so) for knowledge management
