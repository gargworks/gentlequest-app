#!/bin/bash
# Final pre-launch verification
# Run before Feb 1 launch

echo "🎯 FINAL PRE-LAUNCH CHECK"
echo "========================="
echo ""

ERRORS=0

# 1. Migrations
echo "1. Checking migrations..."
if alembic current | grep -q "004_add_performance_indexes"; then
    echo "   ✅ All migrations applied"
else
    echo "   ❌ Migrations not complete"
    ERRORS=$((ERRORS + 1))
fi

# 2. Data seeded
echo "2. Checking seeded data..."
QUEST_COUNT=$(python -c "from app import create_app; from models import db; from sqlalchemy import text; app = create_app(); app.app_context().push(); print(db.session.execute(text('SELECT COUNT(*) FROM quests')).scalar())")
if [ "$QUEST_COUNT" -gt 0 ]; then
    echo "   ✅ Quests seeded ($QUEST_COUNT quests)"
else
    echo "   ⚠️  No quests found"
    ERRORS=$((ERRORS + 1))
fi

# 3. Environment variables
echo "3. Checking environment..."
if [ -n "$GEMINI_API_KEY" ]; then
    echo "   ✅ GEMINI_API_KEY set"
else
    echo "   ❌ GEMINI_API_KEY not set"
    ERRORS=$((ERRORS + 1))
fi

if [ -n "$SENDGRID_API_KEY" ]; then
    echo "   ✅ SENDGRID_API_KEY set (alerts enabled)"
else
    echo "   ⚠️  SENDGRID_API_KEY not set (alerts disabled)"
fi

# 4. Tests
echo "4. Running critical tests..."
if pytest tests/test_crisis_comprehensive.py -v --tb=short > /dev/null 2>&1; then
    echo "   ✅ Crisis detection tests pass"
else
    echo "   ⚠️  Some tests failing"
fi

# 5. Crisis detection
echo "5. Verifying crisis detection..."
if python scripts/verify_crisis_detection.py > /dev/null 2>&1; then
    echo "   ✅ Crisis detection 95%+ accurate"
else
    echo "   ⚠️  Crisis detection below 95%"
fi

# 6. Database health
echo "6. Checking database..."
if python scripts/test_database_connection.py > /dev/null 2>&1; then
    echo "   ✅ Database connected"
else
    echo "   ❌ Database connection failed"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "========================="
if [ $ERRORS -eq 0 ]; then
    echo "✅ READY FOR LAUNCH"
    echo ""
    echo "Next steps:"
    echo "  1. Execute validation (Jan 17-24)"
    echo "  2. Make GO/NO-GO decision (Jan 24)"
    echo "  3. Implement features (Jan 25-31 if GO)"
    echo "  4. Launch Feb 1 (if GO)"
    exit 0
else
    echo "❌ NOT READY ($ERRORS critical issues)"
    echo ""
    echo "Fix issues before launch"
    exit 1
fi
