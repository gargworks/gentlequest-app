#!/bin/bash
# Self-Healing Test Suite for Nucleus CLI
# Triggers various error conditions to validate self-healing behavior

set -u

SYNC_SCRIPT="$(dirname "$0")/terminal_sync.sh"

echo "🧪 Nucleus Self-Healing Test Suite"
echo "===================================="
echo ""

# Test 1: Invalid command
echo "Test 1: Invalid nucleus command"
echo "--------------------------------"
$SYNC_SCRIPT nucleus invalid-command-xyz 2>&1 || true
echo ""

# Test 2: Missing required argument
echo "Test 2: Missing required argument"
echo "----------------------------------"
$SYNC_SCRIPT nucleus task update 2>&1 || true
echo ""

# Test 3: Invalid JSON in tasks file
echo "Test 3: Corrupted tasks.json (if exists)"
echo "-----------------------------------------"
TASKS_FILE="$HOME/.brain/ledger/tasks.json"
if [ -f "$TASKS_FILE" ]; then
    cp "$TASKS_FILE" "$TASKS_FILE.backup"
    echo "INVALID JSON" > "$TASKS_FILE"
    $SYNC_SCRIPT nucleus task list 2>&1 || true
    mv "$TASKS_FILE.backup" "$TASKS_FILE"
    echo "✅ Restored tasks.json"
else
    echo "⏭️  Skipped (no tasks.json found)"
fi
echo ""

# Test 4: Permission denied
echo "Test 4: Permission denied scenario"
echo "-----------------------------------"
TEST_FILE="/tmp/nucleus-test-readonly.txt"
echo "test" > "$TEST_FILE"
chmod 000 "$TEST_FILE"
$SYNC_SCRIPT cat "$TEST_FILE" 2>&1 || true
rm -f "$TEST_FILE"
echo ""

# Test 5: Python import error simulation
echo "Test 5: Import error (simulated)"
echo "---------------------------------"
$SYNC_SCRIPT python3 -c "import nonexistent_module_xyz" 2>&1 || true
echo ""

# Test 6: Brain not initialized
echo "Test 6: Brain not initialized (simulated)"
echo "------------------------------------------"
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"
$SYNC_SCRIPT nucleus status 2>&1 || true
cd - > /dev/null
rm -rf "$TEMP_DIR"
echo ""

echo "===================================="
echo "✅ Test suite complete"
echo "📊 Review /tmp/nucleus-terminal-sync.log for full output"
echo ""
echo "Next steps:"
echo "  1. Run: python3 scripts/monitor_terminal_sync.py tail 100"
echo "  2. Check for self-healing attempts in the log"
echo "  3. Verify error classification and recovery suggestions"
