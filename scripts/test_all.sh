#!/bin/bash
# Run all tests with coverage
# Usage: ./scripts/test_all.sh

set -e

echo "🧪 Running All Tests"
echo "===================="
echo ""

# Backend tests
echo "📦 Backend Tests..."
pytest -v --cov=. --cov-report=term --cov-report=html

echo ""
echo "📊 Coverage Report:"
pytest --cov=. --cov-report=term-missing | tail -20

echo ""
echo "✅ All tests complete"
echo ""
echo "Coverage report: htmlcov/index.html"
