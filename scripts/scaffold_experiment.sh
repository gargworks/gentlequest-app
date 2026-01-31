#!/bin/bash

# Lokesh Studio Experiment Scaffolder
# Automates Phase 1 of the Cellular Mitosis Strategy
# Usage: ./scripts/scaffold_experiment.sh experiment-name

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 experiment-name"
    exit 1
fi

EXP_NAME=$1
# Resolve paths relative to user home and script location
# Assuming script is in ai-mvp-backend/scripts/
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MOTHER_REPO="$(dirname "$SCRIPT_DIR")"
TARGET_ROOT="$HOME/experiments"
TARGET_DIR="$TARGET_ROOT/$EXP_NAME"

echo "🚀 Bootstrapping experiment: $EXP_NAME"
echo "   Source: $MOTHER_REPO"
echo "   Target: $TARGET_DIR"

# 1. Create directory structure
if [ -d "$TARGET_DIR" ]; then
    echo "⚠️  Directory $TARGET_DIR already exists. Aborting to prevent overwrite."
    exit 1
fi

mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/vendor"
mkdir -p "$TARGET_DIR/docs"
mkdir -p "$TARGET_DIR/src"

# 2. Copy Hub Docs (Portable Context)
# We copy explicitly to create a 'Cell Wall' - separate evolution from Main Repo
echo "📄 Injecting Protocols..."
cp "$MOTHER_REPO/AGENTS.md" "$TARGET_DIR/"
cp "$MOTHER_REPO/PROTOCOL.md" "$TARGET_DIR/"
cp "$MOTHER_REPO/CONTEXT_HUB.md" "$TARGET_DIR/"

# 3. Create Experiment-Local Context (The Entrypoint)
echo "🧭 Generating local CONTEXT.md..."
cat <<EOF > "$TARGET_DIR/CONTEXT.md"
# 🧪 Experiment Context: $EXP_NAME

> [!IMPORTANT]
> **Agent Directive:** This is an isolated experiment workspace.
> 1.  **Do not modify** any files outside this directory ($TARGET_DIR).
> 2.  **Memory Isolation**: Do NOT write to the central brain (\`~/ai-mvp-backend/.brain\`). Use \`./notes/\` or \`./docs/\` for all experiment logic.
> 3.  **Refer to** local copies of AGENTS.md and PROTOCOL.md for rules.
> 4.  **Code Patterns**: If you need code from the main repo, ask the user to 'vendor' it into the \`vendor/\` directory. Do not try to import relative paths like \`../../ai-mvp-backend\`.

## 📂 Structure
- \`CONTEXT.md\`: This file (Read First).
- \`brief.md\`: The goal of this experiment.
- \`src/\`: Source code.
- \`vendor/\`: Copied libraries from main repo (Read-Only).
- \`docs/\`: Documentation.

## 🔗 Governance (Copied from Mother Repo)
- [AGENTS.md](./AGENTS.md)
- [PROTOCOL.md](./PROTOCOL.md)
EOF

# 4. Create Placeholder for Brief
echo "📝 Creating experiment brief..."
cat <<EOF > "$TARGET_DIR/brief.md"
# Project Brief: $EXP_NAME

## Vision
[One sentence description of the idea]

## Success Criteria
- [ ] MVP Criteria 1
- [ ] MVP Criteria 2

## Plan
- [ ] Setup (Done)
- [ ] ...
EOF

echo "✅ Ready! To start working:"
echo "   1. Open Workspace: $TARGET_DIR"
echo "   2. Tell Agent: 'Read CONTEXT.md and brief.md'"
