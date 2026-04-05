#!/bin/bash
# Run this script from the json2vault directory to push to GitHub.
# Usage: cd json2vault && bash push_to_github.sh

set -e

echo "=== json2vault → GitHub ==="

# Clean up any stale lock files
rm -f .git/index.lock 2>/dev/null

# Initialize git if needed
if [ ! -d ".git" ]; then
    git init
    git branch -m main
fi

# Stage all files
git add -A

# Commit
git commit -m "Initial commit: json2vault v0.1.0

Turn any JSON data into a structured Obsidian vault.
Supports XHS, Twitter, Weibo, Pocket, and custom formats.
Zero dependencies — pure Python standard library."

# Create GitHub repo (requires gh CLI: brew install gh)
if command -v gh &> /dev/null; then
    gh repo create json2vault --public --source=. --remote=origin --push --description "Turn any JSON data into a structured Obsidian vault"
    echo ""
    echo "Done! Repo: https://github.com/jdh847/json2vault"
else
    echo ""
    echo "gh CLI not found. Create the repo manually:"
    echo "  1. Go to https://github.com/new"
    echo "  2. Name: json2vault"
    echo "  3. Public, no README/LICENSE (already included)"
    echo "  4. Then run:"
    echo ""
    echo "  git remote add origin https://github.com/jdh847/json2vault.git"
    echo "  git push -u origin main"
fi
