"""
Quick test to verify intervention_outcomes table schema on production
"""
import requests

# Test that the table has the new columns
response = requests.get("https://gentlequest.onrender.com/api/health")
print(f"Health: {response.json()}")

# Try to trigger an intervention and check logs
session = "schema-test-12345"
response = requests.post(
    "https://gentlequest.onrender.com/api/chat",
    headers={"Content-Type": "application/json", "X-Session-ID": session},
    json={"message": "I feel anxious"}
)

data = response.json()
print(f"\nResponse type: {data.get('exercise_type')}")
print(f"Offer stage: {data.get('offer_stage', 'NOT IN RESPONSE')}")

# The issue: offer_stage is not being added to the response
# Need to check if it's in the tool_calls result
