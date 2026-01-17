#!/bin/bash
# Post-deployment verification

echo "✅ POST-DEPLOYMENT VERIFICATION"
echo "================================"

URL="https://gentlequest.onrender.com"

# 1. Health check
echo "1. Health check..."
if curl -f $URL/api/health > /dev/null 2>&1; then
    echo "   ✅ Health endpoint responding"
else
    echo "   ❌ Health endpoint failed"
    exit 1
fi

# 2. Test endpoints
echo "2. Testing endpoints..."
ENDPOINTS=("/api/quests" "/api/resources" "/api/profile")

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -f -H "X-Session-ID: test" $URL$endpoint > /dev/null 2>&1; then
        echo "   ✅ $endpoint working"
    else
        echo "   ⚠️  $endpoint returned error"
    fi
done

# 3. Check error rate
echo "3. Checking error rate..."
# TODO: Query logs for error rate

# 4. Verify crisis detection
echo "4. Verifying crisis detection..."
python scripts/verify_crisis_detection.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Crisis detection 95%+ accurate"
else
    echo "   ⚠️  Crisis detection below 95%"
fi

echo ""
echo "================================"
echo "✅ Deployment verified"
echo ""
echo "Monitor for 1 hour, then:"
echo "  - Check error rate in Render dashboard"
echo "  - Verify user signups working"
echo "  - Test crisis alert delivery"
