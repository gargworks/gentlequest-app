#!/bin/bash

# Base URL (assuming local server is running on 5055)
URL="http://127.0.0.1:5055/api/mood_entry"
SESSION_ID="test-user-$(date +%s)"

echo "🧪 Starting Manual Feedback Trigger Test"
echo "   Session ID: $SESSION_ID"
echo "----------------------------------------"

# Function to post mood and check flag
post_mood() {
    count=$1
    echo -n "Step $count: Posting mood... "
    response=$(curl -s -X POST "$URL" \
      -H "Content-Type: application/json" \
      -H "X-Session-ID: $SESSION_ID" \
      -d '{"mood_level": 4, "note": "manual test"}')
    
    # Extract flag using grep/sed for simplicity (no jq required)
    flag=$(echo "$response" | grep -o '"show_feedback_prompt":\s*true' || echo "false")
    
    if [[ "$flag" != "false" ]]; then
        echo "✅ FEEDBACK PROMPT TRIGGERED! (JSON: ... \"show_feedback_prompt\": true ...)"
    else
        echo "   (Normal response)"
    fi
}

# Run 4 times
post_mood 1
post_mood 2
post_mood 3  # Should trigger here
post_mood 4  # Should NOT trigger here

echo "----------------------------------------"
echo "Test Complete."
