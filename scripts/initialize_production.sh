#!/bin/bash
# Initialize production environment
# Run once after first deployment

set -e

echo "🚀 Production Initialization"
echo "============================"
echo ""

# Run migrations
echo "📦 Running migrations..."
alembic upgrade head
echo "✅ Migrations complete"
echo ""

# Seed data
echo "🌱 Seeding data..."
python scripts/seed_quests.py
python scripts/seed_resources.py
echo "⚠️  Update scripts/seed_counselors.py with real contacts before running!"
echo ""

# Create monitoring views
echo "📊 Setting up monitoring..."
python scripts/monitoring_setup.py
echo "✅ Monitoring configured"
echo ""

# Run initial health check
echo "🏥 Health check..."
python scripts/daily_health_check.py
echo ""

# Performance baseline
echo "⚡ Performance baseline..."
python scripts/performance_analysis.py
echo ""

# Security audit
echo "🔒 Security audit..."
python scripts/security_audit.py
echo ""

echo "============================"
echo "✅ Production initialized"
echo ""
echo "Next steps:"
echo "  1. Update counselor contacts in scripts/seed_counselors.py"
echo "  2. Run: python scripts/seed_counselors.py"
echo "  3. Configure SendGrid API key for alerts"
echo "  4. Test crisis alert delivery"
echo "  5. Begin outreach (First 100 Days playbook)"
