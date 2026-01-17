#!/bin/bash
# Production Deployment Script for GentleQuest
# Run with: ./scripts/deploy_production.sh

set -e  # Exit on error

echo "🚀 GentleQuest Production Deployment"
echo "======================================"
echo ""

# Check if on main branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" != "main" ]; then
    echo "⚠️  Warning: Not on main branch (currently on $BRANCH)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "⚠️  Uncommitted changes detected"
    git status -s
    read -p "Commit changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Commit message: " COMMIT_MSG
        git add .
        git commit -m "$COMMIT_MSG"
    else
        exit 1
    fi
fi

# Run tests
echo "🧪 Running tests..."
pytest -v --tb=short
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Aborting deployment."
    exit 1
fi
echo "✅ Tests passed"
echo ""

# Push to main
echo "📤 Pushing to main branch..."
git push origin main
echo "✅ Pushed to GitHub"
echo ""

# Wait for Render auto-deploy
echo "⏳ Waiting for Render deployment (this takes 3-5 minutes)..."
echo "   Monitor at: https://dashboard.render.com"
echo ""
sleep 180  # Wait 3 minutes

# Health check
echo "🏥 Running health check..."
HEALTH_URL="https://gentlequest.onrender.com/api/health"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" $HEALTH_URL)
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check passed"
    echo "$HEALTH_RESPONSE" | head -n-1 | jq '.'
else
    echo "❌ Health check failed (HTTP $HTTP_CODE)"
    echo "$HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Smoke tests
echo "🔥 Running smoke tests..."

# Test quests endpoint
echo "  Testing /api/quests..."
QUESTS_RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-Session-ID: smoke_test" \
    https://gentlequest.onrender.com/api/quests)
QUESTS_CODE=$(echo "$QUESTS_RESPONSE" | tail -n1)

if [ "$QUESTS_CODE" = "200" ]; then
    echo "  ✅ Quests endpoint working"
else
    echo "  ⚠️  Quests endpoint returned $QUESTS_CODE"
fi

# Test resources endpoint
echo "  Testing /api/resources..."
RESOURCES_RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-Session-ID: smoke_test" \
    https://gentlequest.onrender.com/api/resources)
RESOURCES_CODE=$(echo "$RESOURCES_RESPONSE" | tail -n1)

if [ "$RESOURCES_CODE" = "200" ]; then
    echo "  ✅ Resources endpoint working"
else
    echo "  ⚠️  Resources endpoint returned $RESOURCES_CODE"
fi

# Test profile endpoint
echo "  Testing /api/profile..."
PROFILE_RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-Session-ID: smoke_test" \
    https://gentlequest.onrender.com/api/profile)
PROFILE_CODE=$(echo "$PROFILE_RESPONSE" | tail -n1)

if [ "$PROFILE_CODE" = "200" ]; then
    echo "  ✅ Profile endpoint working"
else
    echo "  ⚠️  Profile endpoint returned $PROFILE_CODE"
fi

echo ""
echo "======================================"
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Monitor Render logs for errors"
echo "  2. Check error rate in dashboard"
echo "  3. Verify new features working"
echo "  4. Notify customers of new features (if applicable)"
echo ""
echo "Rollback command (if needed):"
echo "  git revert HEAD && git push origin main"
echo ""
