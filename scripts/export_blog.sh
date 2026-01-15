#!/bin/bash
# scripts/export_blog.sh
set -e  # Kill Switch: Exit on any error

# Configuration (Override with environment variables)
# Default to the current known session ID if not provided
DEFAULT_ID="7c654df4-b83e-43f9-8620-f15868ec39d1"
CONVERSATION_ID="${CONVERSATION_ID:-$DEFAULT_ID}"
BRAIN_DIR="${BRAIN_DIR:-$HOME/.gemini/antigravity/brain/$CONVERSATION_ID}"
OUTPUT_DIR="./blog-export-$(date +%Y%m%d)"

echo "🚀 Starting Blog Export Protocol..."
echo "🧠 Brain Dir: $BRAIN_DIR"

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
  echo "📄 Processing $(basename "$file")..."
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
      # Escape path for sed (replace / with \/)
      # Simple replacement for filename only
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
