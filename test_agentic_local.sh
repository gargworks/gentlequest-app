#!/bin/bash

# Local Docker Test for Agentic Variety Logic
# Memory system disabled to avoid transaction failures

set -e

echo "🐳 Rebuilding Docker with memory disabled..."
docker-compose down
docker-compose up -d --build backend db redis

echo "⏳ Waiting for services to be healthy..."
sleep 20

# Wait for backend health check
for i in {1..15}; do
    if curl -sf http://localhost:5055/api/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy"
        break
    fi
    echo "Waiting for backend... ($i/15)"
    sleep 2
done

echo ""
echo "📊 Testing Agentic Variety Logic (Same Session)"
echo "================================================"

SESSION="local-variety-$(date +%s)"
echo "Session ID: $SESSION"
echo ""

echo "Test 1: First anxiety message"
curl -s -X POST "http://localhost:5055/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{"message": "I feel really anxious"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Stage: {d.get(\"offer_stage\", \"N/A\")} | Type: {d.get(\"exercise_type\", \"N/A\")} | Source: {d.get(\"function_call_source\", \"N/A\")}')
"

sleep 2

echo ""
echo "Test 2: Second anxiety message (same session)"
curl -s -X POST "http://localhost:5055/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{"message": "still feeling anxious"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Stage: {d.get(\"offer_stage\", \"N/A\")} | Type: {d.get(\"exercise_type\", \"N/A\")} | Source: {d.get(\"function_call_source\", \"N/A\")}')
"

sleep 2

echo ""
echo "Test 3: Third anxiety message (same session)"
curl -s -X POST "http://localhost:5055/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{"message": "I am still anxious"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Stage: {d.get(\"offer_stage\", \"N/A\")} | Type: {d.get(\"exercise_type\", \"N/A\")} | Source: {d.get(\"function_call_source\", \"N/A\")}')
"

echo ""
echo "================================================"
echo "✅ Test complete!"
echo ""
echo "Expected Results:"
echo "  Test 1: Stage 1, breathing, keyword_fallback"
echo "  Test 2: Stage 2, grounding, keyword_fallback"
echo "  Test 3: Stage 3, journaling, keyword_fallback"
echo ""
echo "If all show 'keyword_fallback', Gemini isn't calling functions."
echo "But variety logic should still work (Stage 1→2→3)."
echo ""
echo "To stop: docker-compose down"

