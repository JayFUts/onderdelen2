#!/bin/bash

# GitHub Push Script
# Usage: ./push_to_github.sh YOUR_GITHUB_TOKEN

if [ -z "$1" ]; then
    echo "❌ Error: Please provide your GitHub token"
    echo "Usage: ./push_to_github.sh YOUR_GITHUB_TOKEN"
    exit 1
fi

TOKEN=$1
REPO_URL="https://${TOKEN}@github.com/JayFUts/onderdelen2.git"

echo "🚀 Pushing to GitHub..."

# Configure git with token
git remote set-url origin $REPO_URL

# Push to GitHub
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 Repository: https://github.com/JayFUts/onderdelen2"
    echo ""
    echo "🚀 Next steps for Railway deployment:"
    echo "1. Go to https://railway.app"
    echo "2. Sign in with your GitHub account"
    echo "3. Click 'New Project'"
    echo "4. Select 'Deploy from GitHub repo'"
    echo "5. Choose 'JayFUts/onderdelen2'"
    echo "6. Railway will automatically build and deploy!"
    echo ""
    echo "⏱️  Build time: ~5-10 minutes (Chrome installation takes time)"
    echo "🌐 You'll get a URL like: https://onderdelen2-production.up.railway.app"
else
    echo "❌ Failed to push to GitHub"
    echo "Check your token and repository access"
fi