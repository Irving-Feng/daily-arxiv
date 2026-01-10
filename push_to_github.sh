#!/bin/bash

# Script to push commits to GitHub
# Run this in your terminal: bash push_to_github.sh

echo "====================================="
echo "Pushing to GitHub..."
echo "====================================="
echo ""

# Push to GitHub
git push

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Successfully pushed to GitHub!"
    echo ""
    echo "Next steps:"
    echo "1. Go to: https://github.com/Irving-Feng/daily-arxiv/actions"
    echo "2. Click 'Run workflow' to test the updated workflow"
    echo "3. Configure secrets at: https://github.com/Irving-Feng/daily-arxiv/settings/secrets/actions"
else
    echo ""
    echo "✗ Push failed. Please try one of these:"
    echo ""
    echo "Option 1: Enter credentials when prompted"
    echo "  Username: Irving-Feng"
    echo "  Password: Your GitHub Personal Access Token"
    echo ""
    echo "Option 2: Use SSH (if you have SSH keys)"
    echo "  git remote set-url origin git@github.com:Irving-Feng/daily-arxiv.git"
    echo "  git push"
fi
