#!/bin/bash

# Define the script path
SIMULATOR_SCRIPT="$(dirname "$0")/gladiator_simulator.py"

# Check if the simulator script exists
if [ ! -f "$SIMULATOR_SCRIPT" ]; then
    echo "Error: gladiator_simulator.py not found at $SIMULATOR_SCRIPT"
    exit 1
fi

echo "🛡️  Initiating Oracle Truth Audit..."
echo "📜 Loading: .brain/prompts/GENESIS_TRUTH_PROMPT.md"
echo "⚖️  Persona: The Skeptical Critic (Strategy #5)"
echo "---------------------------------------------------"

# Load Environment Variables if available
# 1. Load backend defaults first
if [ -f backend_config.env ]; then
    echo "🔌 Sourcing backend_config.env..."
    set -a
    source backend_config.env
    set +a
fi

# 2. Load local overrides (.env) second (Wins)
if [ -f .env ]; then
    echo "🔌 Sourcing .env..."
    set -a
    source .env
    set +a
fi

# Parse Arguments
AUTO_HEAL=0
PROPOSITION="AUDIT_REQUEST"

# Loop through arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --auto-heal)
      AUTO_HEAL=1
      shift # past argument
      ;;
    *)
      PROPOSITION="$1"
      shift # past argument
      ;;
  esac
done

echo "🔎 Subject: '$PROPOSITION'"

# SMART ARTIFACT RESOLUTION
# If PROPOSITION is not a file, try to find a matching artifact
TARGET_FILE="$PROPOSITION"

if [[ ! -f "$TARGET_FILE" ]]; then
    # Search for files matching the name (case insensitive)
    # Construct search paths dynamically
    SEARCH_PATHS=""
    [ -d ".brain" ] && SEARCH_PATHS="$SEARCH_PATHS .brain"
    [ -d "$GLOBAL_BRAIN" ] && SEARCH_PATHS="$SEARCH_PATHS $GLOBAL_BRAIN"
    SEARCH_PATHS="$SEARCH_PATHS ." # Always include current dir

    # Find matches, filtering out metadata/backup files
    if [ -n "$SEARCH_PATHS" ]; then
        FOUND_FILE=$(find $SEARCH_PATHS -maxdepth 4 -iname "*$PROPOSITION*" -type f -not -path '*/.*' -not -name "*.json" -not -name "*.resolved*" 2>/dev/null | head -n 1)
    fi
    
    if [[ -n "$FOUND_FILE" ]]; then
        echo "✨ Smart Resolve: Input '$PROPOSITION' matched artifact '$FOUND_FILE'"
        TARGET_FILE="$FOUND_FILE"
    fi
fi

# Check if file exists (either provided exact or resolved)
if [[ -f "$TARGET_FILE" ]]; then
    echo "📁 Reading contents from: $TARGET_FILE"
    FILE_CONTENT=$(cat "$TARGET_FILE" | head -200)  # Limit to 200 lines
    
    PROPOSITION="AUDIT FILE: $TARGET_FILE

--- FILE CONTENTS START ---
$FILE_CONTENT
--- FILE CONTENTS END ---

Audit this file's content against the Anti-Hallucination Protocol."
    
    echo "✅ File contents loaded ($(echo "$FILE_CONTENT" | wc -l) lines)"
fi

# Function to run the audit
run_audit() {
    python3 "$SIMULATOR_SCRIPT" "$PROPOSITION" --mode verify_truth --save
}

# Check for Auto-Heal flag
if [ $AUTO_HEAL -eq 1 ]; then
    echo "🩺 Auto-Heal Enabled. Initiating Convergence Loop..."
    MAX_RETRIES=5
    COUNT=1
    
    while [ $COUNT -le $MAX_RETRIES ]; do
        echo "🔄 Iteration $COUNT/$MAX_RETRIES..."
        
        # Run Audit and capture output
        OUTPUT=$(run_audit)
        echo "$OUTPUT"
        
        # Check for Success (Heuristic: Verdict PASS or Confidence 100)
        if echo "$OUTPUT" | grep -q "Verdict: PASS"; then
            echo "✅ Convergence Achieved! Structure Verification Passed."
            exit 0
        fi
        
        echo "⚠️  Structure Verification FAILED. Attempting Surgery..."
        
        # Run Surgeon
        REFLEXION_SCRIPT="$(dirname "$0")/oracle_reflexion.py"
        python3 "$REFLEXION_SCRIPT"
        
        # Increment
        ((COUNT++))
    done
    
    echo "❌ ERROR: Failed to converge after $MAX_RETRIES attempts. Manual intervention required."
    exit 1
else
    # Single Run Mode
    run_audit
fi

echo "---------------------------------------------------"
echo "✅ Audit Complete. Record saved to .brain/decisions/"
