#!/bin/bash
# Validate deployment readiness
# Run before deploying: ./scripts/validate_deployment.sh

echo "✅ DEPLOYMENT VALIDATION"
echo "========================"
echo ""

ERRORS=0

# Check tests pass
echo "🧪 Running tests..."
if pytest -v --tb=short; then
    echo "  ✅ Tests passed"
else
    echo "  ❌ Tests failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check migrations
echo "🗄️  Checking migrations..."
if alembic current > /dev/null 2>&1; then
    echo "  ✅ Migrations OK"
else
    echo "  ❌ Migration issues"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check environment variables
echo "🔐 Checking environment..."
if [ -z "$GEMINI_API_KEY" ]; then
    echo "  ⚠️  GEMINI_API_KEY not set"
    ERRORS=$((ERRORS + 1))
fi

if [ -z "$DATABASE_URL" ]; then
    echo "  ⚠️  DATABASE_URL not set"
    ERRORS=$((ERRORS + 1))
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "dev-secret-key-change-in-production" ]; then
    echo "  ⚠️  SECRET_KEY not set or is default"
    ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
    echo "  ✅ Environment OK"
fi
echo ""

# Summary
if [ $ERRORS -eq 0 ]; then
    echo "✅ READY TO DEPLOY"
    exit 0
else
    echo "❌ NOT READY ($ERRORS issues found)"
    exit 1
fi
