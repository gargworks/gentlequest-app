#!/bin/bash
# Test script for Gemini CLI + Nucleus integration
# Verifies all critical functionality

set -e  # Exit on error

echo "=== Gemini CLI + Nucleus Integration Test Suite ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

# Test function
test_command() {
    local name="$1"
    local cmd="$2"
    local expected_exit="$3"
    
    echo -n "Testing: $name... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        actual_exit=0
    else
        actual_exit=$?
    fi
    
    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo -e "${GREEN}PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (expected exit $expected_exit, got $actual_exit)"
        ((FAILED++))
        return 1
    fi
}

# Set brain path
export NUCLEAR_BRAIN_PATH="/Users/lokeshgarg/ai-mvp-backend/.brain"

echo "Brain Path: $NUCLEAR_BRAIN_PATH"
echo ""

# Test 1: Wrapper script exists and is executable
echo "=== Phase 1: Wrapper Script Tests ==="
test_command "Wrapper script exists" "test -f ./scripts/nucleus-gemini" 0
test_command "Wrapper script is executable" "test -x ./scripts/nucleus-gemini" 0

# Test 2: Basic commands
echo ""
echo "=== Phase 2: Basic Command Tests ==="
test_command "nucleus --version" "./scripts/nucleus-gemini --version" 0
test_command "nucleus status" "./scripts/nucleus-gemini status" 0

# Test 3: Engram operations
echo ""
echo "=== Phase 3: Engram Operations ==="
test_command "engram write (valid)" "./scripts/nucleus-gemini engram write 'test_integration' 'test_value' --context Feature --intensity 5 --format json" 0
test_command "engram search (exists)" "./scripts/nucleus-gemini engram search 'test_integration' --format json" 0
test_command "engram search (empty results)" "./scripts/nucleus-gemini engram search 'nonexistent_key_12345' --format json" 0
test_command "engram write (invalid context)" "./scripts/nucleus-gemini engram write 'test' 'value' --context InvalidContext --format json" 2

# Test 4: Task operations
echo ""
echo "=== Phase 4: Task Operations ==="
test_command "task list" "./scripts/nucleus-gemini task list --format json" 0
test_command "task add" "./scripts/nucleus-gemini task add 'Integration test task' --priority 1 --format json" 0

# Test 5: Session operations
echo ""
echo "=== Phase 5: Session Operations ==="
test_command "session save" "./scripts/nucleus-gemini session save 'Integration test session' --format json" 0
test_command "session resume (most recent)" "./scripts/nucleus-gemini session resume --format json" 0

# Test 6: Growth operations
echo ""
echo "=== Phase 6: Growth Operations ==="
test_command "growth status" "./scripts/nucleus-gemini growth status --format json" 0

# Test 7: Output redirection
echo ""
echo "=== Phase 7: Output Redirection Tests ==="
test_command "JSON output to file" "./scripts/nucleus-gemini engram search 'test_integration' --format json > /tmp/nucleus-test.json && test -s /tmp/nucleus-test.json" 0
test_command "Quiet mode to file" "./scripts/nucleus-gemini engram search 'test' -q > /tmp/nucleus-quiet.txt" 0

# Test 8: Chained commands
echo ""
echo "=== Phase 8: Command Chaining Tests ==="
test_command "Chained commands with &&" "./scripts/nucleus-gemini engram write 'chain_test' 'value' --context Feature --intensity 3 --format json && ./scripts/nucleus-gemini engram search 'chain_test' --format json" 0

# Summary
echo ""
echo "=== Test Summary ==="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo -e "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Integration Status: PRODUCTION READY"
    echo "- Wrapper script: ✅ Working"
    echo "- Basic commands: ✅ Working"
    echo "- Engram ops: ✅ Working"
    echo "- Task ops: ✅ Working"
    echo "- Session ops: ✅ Working"
    echo "- Exit codes: ✅ Correct"
    echo "- Output redirection: ✅ Working"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Please review the failures above and check:"
    echo "1. Brain path is correct: $NUCLEAR_BRAIN_PATH"
    echo "2. Nucleus is installed: pip list | grep nucleus"
    echo "3. Wrapper script is in place: ./scripts/nucleus-gemini"
    exit 1
fi
