#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# LOKESH STUDIO - Shell Aliases & Functions
# ═══════════════════════════════════════════════════════════════════════════
#
# Add this to your ~/.zshrc or ~/.bashrc:
#   source ~/ai-mvp-backend/scripts/studio_aliases.sh
#
# ═══════════════════════════════════════════════════════════════════════════

# Configuration
export STUDIO_HOME="$HOME/ai-mvp-backend"
export EXPERIMENTS_HOME="$HOME/experiments"
export APPS_HOME="$HOME/apps"
export ARCHIVE_HOME="$HOME/archive"

# ───────────────────────────────────────────────────────────────────────────
# NAVIGATION
# ───────────────────────────────────────────────────────────────────────────

# Quick jumps
alias studio='cd $STUDIO_HOME'
alias exps='cd $EXPERIMENTS_HOME'
alias apps='cd $APPS_HOME'
alias archive='cd $ARCHIVE_HOME'

# Open in VS Code / Cursor / Windsurf
alias studio-code='code $STUDIO_HOME'
alias studio-cursor='cursor $STUDIO_HOME'

# ───────────────────────────────────────────────────────────────────────────
# EXPERIMENT MANAGEMENT
# ───────────────────────────────────────────────────────────────────────────

# Create a new experiment (the main command)
# Usage: exp-new my-idea
exp-new() {
    if [ -z "$1" ]; then
        echo "Usage: exp-new <experiment-name>"
        echo "Example: exp-new song-meaning"
        return 1
    fi
    "$STUDIO_HOME/scripts/scaffold_experiment.sh" "$1"
}

# List all experiments
exp-list() {
    echo "📂 Experiments ($EXPERIMENTS_HOME):"
    echo "─────────────────────────────────────"
    ls -la "$EXPERIMENTS_HOME" 2>/dev/null || echo "  (none yet)"
}

# Open an experiment in the default editor
# Usage: exp-open song-meaning
exp-open() {
    if [ -z "$1" ]; then
        echo "Usage: exp-open <experiment-name>"
        exp-list
        return 1
    fi
    cd "$EXPERIMENTS_HOME/$1" && code .
}

# Promote an experiment to an app
# Usage: exp-promote song-meaning
exp-promote() {
    if [ -z "$1" ]; then
        echo "Usage: exp-promote <experiment-name>"
        exp-list
        return 1
    fi
    
    local src="$EXPERIMENTS_HOME/$1"
    local dst="$APPS_HOME/$1"
    
    if [ ! -d "$src" ]; then
        echo "❌ Experiment not found: $src"
        return 1
    fi
    
    if [ -d "$dst" ]; then
        echo "❌ App already exists: $dst"
        return 1
    fi
    
    echo "🚀 Promoting $1 to apps/"
    mv "$src" "$dst"
    cd "$dst"
    git init
    git add .
    git commit -m "Initial commit: promoted from experiment"
    echo "✅ Done! App is now at: $dst"
    echo "   Run 'cd $dst' to start working"
}

# Kill (delete) an experiment
# Usage: exp-kill song-meaning
exp-kill() {
    if [ -z "$1" ]; then
        echo "Usage: exp-kill <experiment-name>"
        exp-list
        return 1
    fi
    
    local target="$EXPERIMENTS_HOME/$1"
    
    if [ ! -d "$target" ]; then
        echo "❌ Experiment not found: $target"
        return 1
    fi
    
    echo "⚠️  This will permanently delete: $target"
    read -p "Are you sure? (y/N) " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        rm -rf "$target"
        echo "✅ Deleted: $1"
    else
        echo "Cancelled."
    fi
}

# ───────────────────────────────────────────────────────────────────────────
# APPS MANAGEMENT
# ───────────────────────────────────────────────────────────────────────────

# List all apps
app-list() {
    echo "📦 Apps ($APPS_HOME):"
    echo "─────────────────────────────────────"
    ls -la "$APPS_HOME" 2>/dev/null || echo "  (none yet)"
}

# Open an app
# Usage: app-open song-meaning
app-open() {
    if [ -z "$1" ]; then
        echo "Usage: app-open <app-name>"
        app-list
        return 1
    fi
    cd "$APPS_HOME/$1" && code .
}

# ───────────────────────────────────────────────────────────────────────────
# ARCHIVE MANAGEMENT
# ───────────────────────────────────────────────────────────────────────────

# Archive a folder (copy to archive with timestamp)
# Usage: archive-add /path/to/old-repo
archive-add() {
    if [ -z "$1" ]; then
        echo "Usage: archive-add /path/to/folder [name]"
        return 1
    fi
    
    local src="$1"
    local name="${2:-$(basename "$src")}"
    local timestamp=$(date +%Y%m%d)
    local dst="$ARCHIVE_HOME/${name}-${timestamp}"
    
    if [ ! -d "$src" ]; then
        echo "❌ Source not found: $src"
        return 1
    fi
    
    echo "📦 Archiving to: $dst"
    cp -r "$src" "$dst"
    echo "✅ Archived! (Original unchanged)"
}

# List archive
archive-list() {
    echo "🗄️  Archive ($ARCHIVE_HOME):"
    echo "─────────────────────────────────────"
    ls -la "$ARCHIVE_HOME" 2>/dev/null || echo "  (empty)"
}

# ───────────────────────────────────────────────────────────────────────────
# HELP
# ───────────────────────────────────────────────────────────────────────────

studio-help() {
    cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════╗
║                    LOKESH STUDIO - QUICK REFERENCE                     ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  NAVIGATION:                                                           ║
║    studio          → cd to Mother Repo                                 ║
║    exps            → cd to experiments/                                ║
║    apps            → cd to apps/                                       ║
║    archive         → cd to archive/                                    ║
║                                                                        ║
║  EXPERIMENTS:                                                          ║
║    exp-new NAME    → Create new experiment                             ║
║    exp-list        → List all experiments                              ║
║    exp-open NAME   → Open experiment in editor                         ║
║    exp-promote NAME→ Move to apps/ and git init                        ║
║    exp-kill NAME   → Delete experiment (with confirm)                  ║
║                                                                        ║
║  APPS:                                                                 ║
║    app-list        → List all apps                                     ║
║    app-open NAME   → Open app in editor                                ║
║                                                                        ║
║  ARCHIVE:                                                              ║
║    archive-add PATH [NAME] → Copy folder to archive                    ║
║    archive-list    → List archived items                               ║
║                                                                        ║
║  DOCS:                                                                 ║
║    ~/ai-mvp-backend/CONTEXT_HUB.md   → The Spine                       ║
║    ~/ai-mvp-backend/STUDIO_MANUAL.md → Full Manual                     ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝
EOF
}

# ───────────────────────────────────────────────────────────────────────────
# INITIALIZATION
# ───────────────────────────────────────────────────────────────────────────

# Create directories if they don't exist
mkdir -p "$EXPERIMENTS_HOME" "$APPS_HOME" "$ARCHIVE_HOME" 2>/dev/null

# Show welcome message on first source (optional)
if [ -z "$STUDIO_INITIALIZED" ]; then
    export STUDIO_INITIALIZED=1
    echo "🎯 Lokesh Studio loaded. Type 'studio-help' for commands."
fi
