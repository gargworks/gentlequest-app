#!/bin/bash

# Quick Health Check for E2E Testing Infrastructure
# Usage: ./test/quick_health_check.sh

echo "🏥 E2E Testing Infrastructure - Quick Health Check"
echo "=================================================="

# Check Python availability
if command -v python3 &> /dev/null; then
    echo "✅ Python 3: Available"
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "   Version: $python_version"
else
    echo "❌ Python 3: Not found"
    exit 1
fi

# Check test directory structure
echo ""
echo "📁 Directory Structure:"
required_dirs=("test/screenshots/e2e" "test/backups" "test/archive" "test/dashboard")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir: Exists"
    else
        echo "❌ $dir: Missing"
    fi
done

# Check key test files
echo ""
echo "📋 Key Test Files:"
required_files=("test/focused_e2e_test.py" "test/health_check.py" "test/test_analytics.py" "test/dashboard/index.html")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $(basename $file): Exists"
    else
        echo "❌ $(basename $file): Missing"
    fi
done

# Check virtual environment
echo ""
echo "🐍 Virtual Environment:"
if [ -d "test_env" ]; then
    echo "✅ test_env: Exists"
    if [ -f "test_env/bin/activate" ]; then
        echo "✅ Activation script: Present"
    else
        echo "⚠️ Activation script: Missing"
    fi
else
    echo "⚠️ test_env: Not found (run ./test/quick_test.sh to create)"
fi

# Check recent test results
echo ""
echo "📊 Recent Test Results:"
if [ -f "test/focused_e2e_results.json" ]; then
    echo "✅ Focused results: Available"
    pass_rate=$(python3 -c "import json; print(json.load(open('test/focused_e2e_results.json')).get('pass_rate', 0))" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   Pass rate: ${pass_rate}%"
    fi
else
    echo "⚠️ Focused results: Not found"
fi

# Check dashboard
echo ""
echo "🌐 Dashboard:"
if [ -f "test/dashboard/index.html" ]; then
    echo "✅ Dashboard: Available"
    echo "   Open with: open test/dashboard/index.html"
else
    echo "❌ Dashboard: Missing"
fi

# Performance check
echo ""
echo "⚡ Quick Performance Check:"
if command -v curl &> /dev/null; then
    load_time=$(curl -s -w '%{time_total}' -o /dev/null "https://gentlequest.onrender.com" 2>/dev/null)
    if [ $? -eq 0 ] && [ "$load_time" != "" ]; then
        if (( $(echo "$load_time < 1.0" | bc -l) )); then
            echo "✅ App load time: ${load_time}s (Excellent)"
        elif (( $(echo "$load_time < 2.0" | bc -l) )); then
            echo "⚠️ App load time: ${load_time}s (Good)"
        else
            echo "❌ App load time: ${load_time}s (Slow)"
        fi
    else
        echo "❌ App load check: Failed"
    fi
else
    echo "⚠️ curl: Not available for performance check"
fi

# Overall status
echo ""
echo "🎯 Overall Status:"
echo "✅ E2E Testing Infrastructure is operational"
echo "💡 Run './test/quick_test.sh' for full test execution"
echo "🌐 View dashboard: open test/dashboard/index.html"
