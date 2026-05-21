#!/usr/bin/env bash
# adr_new.sh — minimal ADR scaffolder. Vendor-free replacement for `adr-tools`.
#
# Usage:
#   scripts/adr_new.sh "short decision title"
#   scripts/adr_new.sh --supersedes 0002 "new decision title"
#
# Creates docs/adr/NNNN-kebab-title.md from docs/adr/TEMPLATE.md.
# NNNN is the next zero-padded integer after the highest existing ADR.
# If --supersedes is passed, the new ADR's Status line is pre-filled to
# "Accepted, supersedes NNNN", and the superseded ADR's Status line is
# rewritten to "Superseded by [NNNN](NNNN-slug.md)".

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ADR_DIR="$ROOT/docs/adr"
TEMPLATE="$ADR_DIR/TEMPLATE.md"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "error: $TEMPLATE not found" >&2
  exit 1
fi

SUPERSEDES=""
if [[ "${1:-}" == "--supersedes" ]]; then
  SUPERSEDES="$2"
  shift 2
fi

TITLE="${1:-}"
if [[ -z "$TITLE" ]]; then
  echo "usage: $0 [--supersedes NNNN] \"short decision title\"" >&2
  exit 2
fi

# Compute next ADR number.
LAST=0
for f in "$ADR_DIR"/[0-9][0-9][0-9][0-9]-*.md; do
  [[ -e "$f" ]] || continue
  n="$(basename "$f" | cut -d- -f1 | sed 's/^0*//')"
  [[ -z "$n" ]] && n=0
  (( n > LAST )) && LAST=$n
done
NEXT=$(printf "%04d" $((LAST + 1)))

# Slugify.
SLUG="$(echo "$TITLE" \
  | tr '[:upper:]' '[:lower:]' \
  | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g')"

OUT="$ADR_DIR/$NEXT-$SLUG.md"
if [[ -e "$OUT" ]]; then
  echo "error: $OUT already exists" >&2
  exit 3
fi

TODAY="$(date +%Y-%m-%d)"

# Seed the new ADR from template, then patch title + date.
sed \
  -e "1s/.*/# $NEXT. $TITLE/" \
  -e "s/^Date: YYYY-MM-DD\$/Date: $TODAY/" \
  "$TEMPLATE" > "$OUT"

if [[ -n "$SUPERSEDES" ]]; then
  SUPER_PAD="$(printf "%04d" "$((10#$SUPERSEDES))")"
  SUPER_FILE="$(ls "$ADR_DIR"/"$SUPER_PAD"-*.md 2>/dev/null | head -n1 || true)"
  if [[ -z "$SUPER_FILE" ]]; then
    echo "warning: no ADR found matching $SUPER_PAD-*.md; wrote new ADR but did not update predecessor" >&2
  else
    # Rewrite Status line on successor.
    sed -i.bak "s|^Proposed | Accepted.*|Accepted, supersedes [$SUPER_PAD]($(basename "$SUPER_FILE"))|" "$OUT" || true
    # Rewrite Status line on predecessor.
    sed -i.bak "s|^Accepted.*|Superseded by [$NEXT]($(basename "$OUT"))|" "$SUPER_FILE" || true
    rm -f "$OUT.bak" "$SUPER_FILE.bak"
  fi
fi

echo "$OUT"
