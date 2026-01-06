#!/bin/bash
# Nightly Agent Wrapper (MDR_005 Compliant)
# Ensures environment variables are loaded before running the Nucleus Agent Runtime

PROJECT_ROOT="/Users/lokeshgarg/ai-mvp-backend"
cd "$PROJECT_ROOT"

# Load environment variables properly
set -a
source "$PROJECT_ROOT/.env"
set +a

# Run the NAR-based nightly agent
/usr/bin/python3 "$PROJECT_ROOT/scripts/nightly_agent.py"
