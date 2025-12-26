#!/bin/bash
# Quick variety test - use SAME session for all 3 tests

# Create session ONCE
SESSION="variety-test-$(date +%s)"
echo "Using session: $SESSION"
echo ""

# Test 1
echo "Test 1: First anxiety message"
curl -s -X POST "https://gentlequest.onrender.com/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{"message": "I feel anxious"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Stage: {d.get(\"offer_stage\")} | Type: {d.get(\"exercise_type\")} | Source: {d.get(\"function_call_source\")}')"

sleep 2

# Test 2 - SAME SESSION
echo "Test 2: Still anxious (same session)"
curl -s -X POST "https://gentlequest.onrender.com/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{"message": "still feeling anxious"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Stage: {d.get(\"offer_stage\")} | Type: {d.get(\"exercise_type\")} | Source: {d.get(\"function_call_source\")}')"

sleep 2

# Test 3 - SAME SESSION
echo "Test 3: Still anxious (same session)"
curl -s -X POST "https://gentlequest.onrender.com/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: $SESSION" \
  -d '{"message": "I am still anxious"}' | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  Stage: {d.get(\"offer_stage\")} | Type: {d.get(\"exercise_type\")} | Source: {d.get(\"function_call_source\")}')"

echo ""
echo "Expected: Stage 1→2→3, Type breathing→grounding→journaling"
