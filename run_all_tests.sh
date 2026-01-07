#!/bin/bash
# Automated test script for Daily arXiv Paper Collection System
# Tests all major components before deployment

echo "=========================================="
echo "Daily arXiv System - Component Tests"
echo "=========================================="
echo ""

# Track test results
FAILED_TESTS=0

# Test 1: Notion API
echo "1. Testing Notion API Connection..."
echo "------------------------------------------"
python test_notion.py
if [ $? -ne 0 ]; then
    echo "✗ Notion API test FAILED!"
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    echo "✓ Notion API test PASSED!"
fi
echo ""

# Test 2: papers.cool scraper
echo "2. Testing papers.cool Scraper..."
echo "------------------------------------------"
python test_papers_cool.py
if [ $? -ne 0 ]; then
    echo "✗ papers.cool scraper test FAILED!"
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    echo "✓ papers.cool scraper test PASSED!"
fi
echo ""

# Test 3: arXiv API
echo "3. Testing arXiv API Client..."
echo "------------------------------------------"
python test_arxiv.py --search
if [ $? -ne 0 ]; then
    echo "✗ arXiv API test FAILED!"
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    echo "✓ arXiv API test PASSED!"
fi
echo ""

# Test 4: LLM (OpenAI) - test summary only (faster)
echo "4. Testing LLM Report Generation..."
echo "------------------------------------------"
python test_llm.py --test summary
if [ $? -ne 0 ]; then
    echo "✗ LLM test FAILED!"
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    echo "✓ LLM test PASSED!"
fi
echo ""

# Final summary
echo "=========================================="
echo "Test Summary"
echo "=========================================="

if [ $FAILED_TESTS -eq 0 ]; then
    echo "✓ All tests PASSED!"
    echo ""
    echo "Your system is ready to deploy to GitHub Actions!"
    echo ""
    echo "Next steps:"
    echo "1. Run a full end-to-end test:"
    echo "   python main.py --mode daily --date 2026-01-05"
    echo ""
    echo "2. If the end-to-end test succeeds, push to GitHub:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/daily-arxiv.git"
    echo "   git push -u origin main"
    exit 0
else
    echo "✗ $FAILED_TESTS test(s) FAILED!"
    echo ""
    echo "Please fix the issues above before deploying."
    echo "Check the error messages and verify your .env configuration."
    exit 1
fi
