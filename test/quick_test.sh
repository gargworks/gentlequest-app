#!/bin/bash
# Quick E2E Test Runner for GentleQuest
echo "🚀 Setting up E2E test environment..."

# Create virtual environment
python3 -m venv test_env
source test_env/bin/activate

# Install dependencies
pip install -r test/requirements.txt

# Install Playwright browsers
python3 -m playwright install chromium

# Run focused E2E tests
echo "🧪 Running E2E tests..."
python3 test/focused_e2e_test.py

echo "✅ Test complete! Check test/screenshots/e2e/ for results"
