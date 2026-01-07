# GitHub Actions Setup Guide

## Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (e.g., `daily-arxiv`)
3. Don't initialize with README (we already have code)
4. Click "Create repository"

## Step 2: Push Code to GitHub

Run these commands in your terminal:

```bash
# Add remote repository (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/daily-arxiv.git

# Push to GitHub
git push -u origin main
```

## Step 3: Configure GitHub Secrets

Go to your repository on GitHub and set up the following secrets:

**Navigate to**: Settings → Secrets and variables → Actions → New repository secret

### Required Secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `OPENAI_BASE_URL` | OpenAI API base URL (if using custom) | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | Model to use for report generation | `gpt-4o` |
| `OPENAI_MAX_TOKENS` | Maximum tokens for LLM response | `8192` |
| `OPENAI_TEMPERATURE` | Temperature for LLM | `0.7` |
| `NOTION_API_KEY` | Your Notion integration token | `secret_...` |
| `NOTION_DATABASE_ID` | Notion database ID | `32-char-id` |
| `NOTION_PARENT_PAGE_ID` | Parent page ID for reports | `32-char-id` |

### How to Get Notion Credentials:

1. **Create Integration**: https://www.notion.so/my-integrations
   - Click "New integration"
   - Give it a name (e.g., "Daily arXiv")
   - Select your workspace
   - Copy the "Internal Integration Token" → `NOTION_API_KEY`

2. **Create Database**:
   - Create a new page in Notion
   - Add a database (Table view)
   - Click "⋯" on the database → "Add connections"
   - Select your integration
   - Copy the Database ID from URL: `https://notion.so/{DATABASE_ID}?v=...`
   - Also copy the page ID from URL → `NOTION_PARENT_PAGE_ID`

## Step 4: Test GitHub Actions

### Option A: Manual Trigger (Recommended for testing)

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Daily arXiv Paper Collection" workflow
4. Click "Run workflow"
5. Select mode: `daily`, `weekly`, or `monthly`
6. Optionally specify a date (YYYY-MM-DD)
7. Click "Run workflow"

### Option B: Wait for Scheduled Run

The workflows will run automatically:
- **Daily**: 6:00 AM Beijing time (10:00 PM UTC previous day)
- **Weekly**: Sundays at 6:00 AM Beijing time
- **Monthly**: Last day of month at 6:00 AM Beijing time

## Step 5: Monitor Execution

1. Go to "Actions" tab
2. Click on the workflow run
3. View logs for each step
4. Check your Notion database for generated reports

## Troubleshooting

### Workflow fails to start
- Check that secrets are correctly configured
- Verify GitHub Actions is enabled (Settings → Actions → General)

### Playwright not found
- The workflow installs it automatically via `pip install playwright`
- If issues occur, check the "Install dependencies" step logs

### Timeout errors
- Daily workflow has 60-minute timeout
- If processing many papers, consider increasing `timeout-minutes`

### Notion API errors
- Verify `NOTION_API_KEY` is correct
- Ensure database is shared with your integration
- Check `NOTION_DATABASE_ID` and `NOTION_PARENT_PAGE_ID` are correct

### LLM API errors
- Verify `OPENAI_API_KEY` is valid
- Check if you have available credits/quota
- Ensure `OPENAI_BASE_URL` is correct (if using custom endpoint)

## Local Testing

Before running on GitHub Actions, test locally:

```bash
# Test daily collection
python main.py --mode daily --date 2026-01-06

# Test weekly summary
python main.py --mode weekly

# Test monthly summary
python main.py --mode monthly
```

## Workflow Files

- `.github/workflows/daily-arxiv.yml` - Daily paper collection
- `.github/workflows/weekly-summary.yml` - Weekly summary
- `.github/workflows/monthly-summary.yml` - Monthly summary

Each workflow can be manually triggered with different modes.
