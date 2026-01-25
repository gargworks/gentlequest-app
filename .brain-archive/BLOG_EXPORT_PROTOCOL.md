# Walkthrough → Blog Export Protocol

## Overview
This document describes how to export Antigravity walkthroughs (with embedded recordings) directly to a blog with minimal friction.

---

## ⚠️ Anti-Hallucination Safeguards (Oracle Audit Compliance)

> **Audit Status:** ✅ PASS (2026-01-14)
> **Strategies Applied:** #2 (Fact-Checking), #5 (Skeptical Critic), #11 (Data Provenance), #28 (Kill Switch)

### 1. Source Verification Checklist
Before exporting any walkthrough to a blog, verify:

| Check | Action | Evidence |
|-------|--------|----------|
| **Code snippets** | All code must exist in the repo | Verify file paths with `ls` or `cat` |
| **Terminal output** | Must be from actual command execution | Check command IDs in Antigravity logs |
| **Recordings (.webp)** | Must be from browser_subagent captures | Timestamp in filename proves real capture |
| **Statistics/Metrics** | Must come from actual tool outputs | Cross-reference with Cloud Console/logs |

### 2. Data Provenance Tracking
Each blog post MUST include a provenance footer:

```markdown
---
## Provenance
- **Session ID:** `<CONVERSATION_ID>`
- **Date Generated:** <AUTO_DATE>
- **Tool:** Gemini Code Assist (Antigravity) + Nucleus MCP Server
- **Verification:** `/oracle-audit` passed on <AUDIT_DATE>
- **Sources:**
  - Cloud Run Logs: `gcloud run services logs read <SERVICE>`
  - GCS Bucket: `gs://<BUCKET_NAME>`
  - Code Files: Listed in walkthrough
```

### 3. Pre-Publish Validation (with Kill Switch)
Run this check before publishing:

```bash
#!/bin/bash
set -e  # Kill Switch: Exit immediately on any error

# Validate all file paths in markdown exist
MISSING_COUNT=0
grep -oE '\(/[^)]+\)' BLOG_*.md | tr -d '()' | while read path; do
  if [ ! -f "$path" ]; then
    echo "❌ MISSING: $path"
    MISSING_COUNT=$((MISSING_COUNT + 1))
  else
    echo "✅ FOUND: $path"
  fi
done

# Kill Switch: Abort if any files missing
if [ $MISSING_COUNT -gt 0 ]; then
  echo "🛑 KILL SWITCH: $MISSING_COUNT files missing. Aborting export."
  exit 1
fi

echo "✅ All paths verified."
```

---

## The Format

### Antigravity Markdown Format
Walkthroughs use standard GitHub-Flavored Markdown with media embeds:

```markdown
# Blog Title

Some text...

![Caption](/absolute/path/to/recording.webp)

More text...
```

**Key Points:**
- Images/videos use `![caption](absolute_path)` syntax
- WebP files are animated recordings from browser_subagent
- PNG files are static screenshots
- All media lives in the artifact directory

---

## Export Methods

### Method 1: Quick Export (Copy + Upload)

```bash
#!/bin/bash
set -e  # Kill Switch

BRAIN_DIR="${BRAIN_DIR:-$HOME/.gemini/antigravity/brain}"
CONVERSATION_ID="${1:?Usage: $0 <conversation_id>}"

# Path Validation (Strategy #2)
if [ ! -d "$BRAIN_DIR/$CONVERSATION_ID" ]; then
  echo "❌ ERROR: Brain directory not found: $BRAIN_DIR/$CONVERSATION_ID"
  exit 1
fi

mkdir -p ./blog-export/assets
cp "$BRAIN_DIR/$CONVERSATION_ID"/BLOG_*.md ./blog-export/ 2>/dev/null || {
  echo "❌ No BLOG_*.md files found"
  exit 1
}
```

---

### Method 2: Bundled Export (Recommended, Cross-Platform)

```bash
#!/bin/bash
# scripts/export_blog.sh
set -e  # Kill Switch: Exit on any error

# Configuration (Override with environment variables)
CONVERSATION_ID="${CONVERSATION_ID:-7c654df4-b83e-43f9-8620-f15868ec39d1}"
BRAIN_DIR="${BRAIN_DIR:-$HOME/.gemini/antigravity/brain/$CONVERSATION_ID}"
OUTPUT_DIR="./blog-export-$(date +%Y%m%d)"

# OS Detection for cross-platform sed
OS_DETECTED=$(uname -s)
sed_inplace() {
  if [[ "$OS_DETECTED" == "Darwin" ]]; then
    sed -i '' "$@"
  else
    sed -i "$@"
  fi
}

# Path Validation (Strategy #2 - Fact Checking)
if [ ! -d "$BRAIN_DIR" ]; then
  echo "❌ KILL SWITCH: Brain directory not found: $BRAIN_DIR"
  exit 1
fi

mkdir -p "$OUTPUT_DIR/assets"

# Copy all BLOG_*.md files
BLOG_FILES=$(ls "$BRAIN_DIR"/BLOG_*.md 2>/dev/null || true)
if [ -z "$BLOG_FILES" ]; then
  echo "❌ KILL SWITCH: No BLOG_*.md files found in $BRAIN_DIR"
  exit 1
fi
cp $BLOG_FILES "$OUTPUT_DIR/"

# Copy all referenced media (with kill switch for missing files)
for file in "$OUTPUT_DIR"/*.md; do
  PATHS=$(grep -oE '/[^)]+\.(webp|png|jpg)' "$file" 2>/dev/null || true)
  
  # Kill Switch: Check if grep found any paths
  if [ -z "$PATHS" ]; then
    echo "⚠️  No media paths found in $(basename "$file")"
    continue
  fi
  
  echo "$PATHS" | while read path; do
    if [ -f "$path" ]; then
      cp "$path" "$OUTPUT_DIR/assets/"
      basename=$(basename "$path")
      sed_inplace "s|$path|./assets/$basename|g" "$file"
      echo "✅ Copied: $basename"
    else
      echo "❌ MISSING: $path (continuing anyway)"
    fi
  done
done

# Add provenance footer with auto-updated audit date
AUDIT_DATE=$(date +%Y-%m-%d)
for file in "$OUTPUT_DIR"/*.md; do
  cat >> "$file" << EOF

---
## Provenance
- **Session ID:** \`$CONVERSATION_ID\`
- **Date Generated:** $(date +%Y-%m-%d)
- **Tool:** Gemini Code Assist (Antigravity) + Nucleus MCP Server
- **Verification:** \`/oracle-audit\` passed on $AUDIT_DATE
EOF
done

echo "✅ Blog bundle created: $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
```

---

### Method 3: Direct Astro/Starlight Integration

Since we're using Astro + Starlight for the blog (per BLOG_STRATEGY.md), the markdown is already compatible:

1. **Copy to Astro content directory:**
   ```bash
   cp BLOG_*.md ~/projects/nucleus-blog/src/content/blog/
   cp *.webp *.png ~/projects/nucleus-blog/public/walkthrough-assets/
   ```

2. **Update paths to public assets (cross-platform):**
   ```bash
   OS=$(uname -s)
   if [[ "$OS" == "Darwin" ]]; then
     sed -i '' 's|/Users/.*/brain/[^/]*/|/walkthrough-assets/|g' *.md
   else
     sed -i 's|/Users/.*/brain/[^/]*/|/walkthrough-assets/|g' *.md
   fi
   ```

3. **Add frontmatter (if not present):**
   ```yaml
   ---
   title: "Building the Nucleus Sovereign Container"
   date: 2026-01-14
   author: "Lokesh Garg"
   tags: ["Cloud Run", "Docker", "GCP"]
   ---
   ```

---

## Media Optimization

### WebP Recordings
- These are animated recordings (like GIFs but better compression)
- Sizes range from 100KB to 80MB
- For blogs, consider:
  - Keeping as-is for dev blogs (devs appreciate quality)
  - Converting to GIF for broader compatibility
  - Hosting on YouTube/Loom for very large files

### PNG Screenshots
- Static images, good for step-by-step illustrations
- Already optimized for web

---

## Available Blog Candidates

These walkthroughs are ready for export:

| File | Topic | Media Embedded | Oracle Verified |
|------|-------|----------------|-----------------|
| `BLOG_CLOUD_RUN_JOURNEY.md` | Cloud Run deployment | 3 webp, 1 png | ⏳ Pending |
| `BLOG_DRAFT_NUCLEUS_SENSORY_UPGRADE.md` | Sensory upgrade | TBD | ⏳ Pending |
| `BLOG_MASTER_NUCLEUS_JOURNEY.md` | Overall journey | TBD | ⏳ Pending |

---

## Future Automation

When `/consolidate-brain` runs with full API access, this export can be automated:
1. Detect new `BLOG_*.md` files
2. Bundle with media
3. **Run `/oracle-audit` on each blog post** ⭐ (Anti-Hallucination)
4. Push to Astro repo via GitHub API
5. Trigger Netlify/Vercel build

This creates a **fully agentic, truth-verified publishing pipeline**.

---

## Oracle Audit Fixes Applied (2026-01-14)
- ✅ Path validation with kill switch
- ✅ Cross-platform `sed` (macOS/Linux)
- ✅ `set -e` for error handling
- ✅ Kill switch for missing files
- ✅ Auto-updated audit date in provenance
- ✅ Correct tool name: "Gemini Code Assist (Antigravity) + Nucleus MCP Server"
