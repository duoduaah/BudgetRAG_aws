#!/bin/bash
set -e

echo "======================================"
echo "Running Test Suite"
echo "======================================"

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -q -r requirements-dev.txt

echo ""
echo "🧪 Running tests..."
pytest

echo ""
echo "======================================"
echo "✅ Tests Complete!"
echo "======================================"
echo ""
echo "📊 Coverage report generated in: htmlcov/index.html"
echo "   Open with: open htmlcov/index.html"
echo "======================================"
