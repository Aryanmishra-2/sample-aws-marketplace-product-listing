#!/bin/bash
# Repository cleanup script
# Removes temporary files and caches

echo "🧹 Cleaning up repository..."

# Remove Python cache files
echo "  Removing __pycache__ directories..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc files
echo "  Removing .pyc files..."
find . -name "*.pyc" -type f -delete 2>/dev/null || true

# Remove .DS_Store files (macOS)
echo "  Removing .DS_Store files..."
find . -name ".DS_Store" -type f -delete 2>/dev/null || true

# Remove temporary files
echo "  Removing temporary files..."
find . -name "*.tmp" -type f -delete 2>/dev/null || true
find . -name "*.bak" -type f -delete 2>/dev/null || true

# Remove log files
echo "  Removing log files..."
find . -name "*.log" -type f -delete 2>/dev/null || true

# Remove coverage files
echo "  Removing coverage files..."
rm -rf .coverage htmlcov/ 2>/dev/null || true

echo "✅ Cleanup complete!"