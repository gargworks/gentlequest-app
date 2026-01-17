#!/bin/bash
# Rollback Script for GentleQuest
# Run with: ./scripts/rollback_deployment.sh

set -e

echo "🔄 GentleQuest Deployment Rollback"
echo "======================================"
echo ""

# Confirm rollback
read -p "Are you sure you want to rollback? (yes/no) " -r
echo
if [[ ! $REPLY = "yes" ]]; then
    echo "Rollback cancelled"
    exit 0
fi

# Get last commit
LAST_COMMIT=$(git log --oneline -1)
echo "Current commit: $LAST_COMMIT"
echo ""

# Revert last commit
echo "⏪ Reverting last commit..."
git revert HEAD --no-edit

# Push revert
echo "📤 Pushing revert to main..."
git push origin main

echo "✅ Code rollback complete"
echo ""

# Rollback database migrations (if needed)
read -p "Rollback database migrations? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗄️  Rolling back migrations..."
    echo "   Run in Render Shell:"
    echo "   alembic downgrade -1"
    echo ""
    echo "   Or rollback all new migrations:"
    echo "   alembic downgrade -3"
fi

echo ""
echo "======================================"
echo "✅ Rollback initiated"
echo ""
echo "Monitor deployment at: https://dashboard.render.com"
echo "Verify health: curl https://gentlequest.onrender.com/api/health"
echo ""
