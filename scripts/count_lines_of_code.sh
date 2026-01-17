#!/bin/bash
# Count lines of code in project

echo "📊 LINES OF CODE"
echo "================"
echo ""

echo "Python (Backend):"
find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -not -path "./checkpoints/*" | xargs wc -l | tail -1

echo ""
echo "Dart (Frontend):"
find ai_buddy_web/lib -name "*.dart" | xargs wc -l | tail -1

echo ""
echo "SQL:"
find . -name "*.sql" | xargs wc -l | tail -1

echo ""
echo "Shell Scripts:"
find scripts -name "*.sh" | xargs wc -l | tail -1

echo ""
echo "Total Project:"
find . -name "*.py" -o -name "*.dart" -o -name "*.sql" -o -name "*.sh" | grep -v venv | grep -v checkpoints | xargs wc -l | tail -1
