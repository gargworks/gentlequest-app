#!/bin/bash
# Backup critical project data to external SSD
# Usage: .brain/backup_ssd.sh [volume_name]
#
# What gets backed up:
#   1. .brain/          — the family's memory (most critical)
#   2. ai-mvp-backend/  — entire project (code, configs, scripts)
#   3. ~/.claude/        — Claude Code sessions, memory, transcripts
#
# Uses rsync (incremental) — first run copies everything, subsequent runs only sync changes.
# Typical incremental run: <30 seconds for a few changed files.

set -e

# ── Config ──
SSD_NAME="${1:-Samsung SSD 990 PRO 2TB Media}"
SSD_PATH="/Volumes/$SSD_NAME"
BACKUP_ROOT="$SSD_PATH/nucleus-backup"
PROJECT_DIR="/Users/lokeshgarg/ai-mvp-backend"
APPS_DIR="/Users/lokeshgarg/apps"
CLAUDE_DIR="/Users/lokeshgarg/.claude"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# ── Preflight ──
if [ ! -d "$SSD_PATH" ]; then
    echo "❌ SSD not found at $SSD_PATH"
    echo "   Plug in your SSD or specify volume name: $0 <volume_name>"
    echo "   Available volumes:"
    ls /Volumes/
    exit 1
fi

echo "🧠 Nucleus Backup → $SSD_PATH"
echo "   $(date)"
echo ""

# ── Create backup structure ──
mkdir -p "$BACKUP_ROOT/brain"
mkdir -p "$BACKUP_ROOT/project"
mkdir -p "$BACKUP_ROOT/claude"

# ── 1. Brain (most critical — the family's memory) ──
echo "📦 Syncing .brain/ ..."
rsync -az --delete \
    --exclude '.DS_Store' \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    "$PROJECT_DIR/.brain/" "$BACKUP_ROOT/brain/"
echo "   ✅ Brain synced"

# ── 2. Full project ──
echo "📦 Syncing ai-mvp-backend/ ..."
rsync -az --delete \
    --exclude '.DS_Store' \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude '.venv/' \
    --exclude 'node_modules/' \
    --exclude '.git/objects/' \
    --exclude '.brain-backup-*' \
    "$PROJECT_DIR/" "$BACKUP_ROOT/project/"
echo "   ✅ Project synced"

# ── 3. Apps (believe-it-bot, future projects) ──
# Skip: symlinks (weights already on SSD), venvs (recreatable)
echo "📦 Syncing ~/apps/ ..."
mkdir -p "$BACKUP_ROOT/apps"
rsync -az --delete --no-links \
    --exclude '.DS_Store' \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude 'venv/' \
    --exclude 'venv_xtts/' \
    --exclude 'node_modules/' \
    --exclude '.git/objects/' \
    "$APPS_DIR/" "$BACKUP_ROOT/apps/"
echo "   ✅ Apps synced (symlinks skipped — weights already on SSD)"

# ── 4. Claude Code sessions & memory ──
echo "📦 Syncing ~/.claude/ ..."
rsync -az --delete \
    --exclude '.DS_Store' \
    "$CLAUDE_DIR/" "$BACKUP_ROOT/claude/"
echo "   ✅ Claude sessions synced"

# ── Write manifest ──
cat > "$BACKUP_ROOT/MANIFEST.json" << MANIFEST
{
  "timestamp": "$TIMESTAMP",
  "machine": "$(hostname)",
  "os": "$(sw_vers -productVersion 2>/dev/null || echo unknown)",
  "contents": {
    "brain": "$BACKUP_ROOT/brain",
    "project": "$BACKUP_ROOT/project",
    "apps": "$BACKUP_ROOT/apps",
    "claude": "$BACKUP_ROOT/claude"
  },
  "sizes": {
    "brain": "$(du -sh "$BACKUP_ROOT/brain" | cut -f1)",
    "project": "$(du -sh "$BACKUP_ROOT/project" | cut -f1)",
    "apps": "$(du -sh "$BACKUP_ROOT/apps" | cut -f1)",
    "claude": "$(du -sh "$BACKUP_ROOT/claude" | cut -f1)"
  }
}
MANIFEST

# ── Write local breadcrumb (so heartbeat can check without SSD mounted) ──
mkdir -p "$PROJECT_DIR/.brain/heartbeat"
cat > "$PROJECT_DIR/.brain/heartbeat/last_ssd_backup.json" << BREADCRUMB
{
  "timestamp": "$TIMESTAMP",
  "iso": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ssd": "$SSD_NAME",
  "sizes": {
    "brain": "$(du -sh "$BACKUP_ROOT/brain" | cut -f1)",
    "project": "$(du -sh "$BACKUP_ROOT/project" | cut -f1)",
    "apps": "$(du -sh "$BACKUP_ROOT/apps" | cut -f1)",
    "claude": "$(du -sh "$BACKUP_ROOT/claude" | cut -f1)"
  }
}
BREADCRUMB

echo ""
echo "✅ Backup complete → $BACKUP_ROOT"
echo "   Brain:   $(du -sh "$BACKUP_ROOT/brain" | cut -f1)"
echo "   Project: $(du -sh "$BACKUP_ROOT/project" | cut -f1)"
echo "   Apps:    $(du -sh "$BACKUP_ROOT/apps" | cut -f1)"
echo "   Claude:  $(du -sh "$BACKUP_ROOT/claude" | cut -f1)"
echo "   Total:   $(du -sh "$BACKUP_ROOT" | cut -f1)"
echo ""
echo "   To restore on a new machine:"
echo "   rsync -az $BACKUP_ROOT/brain/ /path/to/.brain/"
echo "   rsync -az $BACKUP_ROOT/project/ /path/to/ai-mvp-backend/"
echo "   rsync -az $BACKUP_ROOT/apps/ ~/apps/"
echo "   rsync -az $BACKUP_ROOT/claude/ ~/.claude/"
