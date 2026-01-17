#!/bin/bash
# Quick deploy without full validation (use with caution)
set -e

echo "⚡ QUICK DEPLOY"
echo "==============="

git add .
git commit -m "${1:-Quick deploy}"
git push origin main

echo "✅ Pushed to main. Render will auto-deploy in 3-5 minutes."
echo "Monitor: https://dashboard.render.com"
