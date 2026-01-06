#!/bin/bash
# Brain Backup Script
# Run this weekly or before major work sessions

set -e  # Exit on error

echo "🧠 Backing up Antigravity brain..."

# Copy to Git repo
cp -r ~/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/ \
  /Users/lokeshgarg/ai-mvp-backend/.brain-archive/

# Copy to Google Drive (Only if --monthly flag is passed)
if [[ "$1" == "--monthly" ]]; then
  echo "☁️  Monthly Backup: Copying to Google Drive..."
  cp -r ~/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/ \
    "/Users/lokeshgarg/Library/CloudStorage/GoogleDrive-mailforlkgarg@gmail.com/My Drive/nucleus-brain-backup/"
else
  echo "⏩ Skipping Google Drive (Weekly Git backup only). Use --monthly to include Drive."
fi

# Commit to Git (Always)
cd /Users/lokeshgarg/ai-mvp-backend
git add .brain-archive/
git commit -m "backup: Brain snapshot $(date +%Y-%m-%d)" || echo "No changes to commit"
git push

echo ""
echo "✅ Backup complete!"
echo "📍 Git: /ai-mvp-backend/.brain-archive/"
echo "☁️  Google Drive: /My Drive/nucleus-brain-backup/"
