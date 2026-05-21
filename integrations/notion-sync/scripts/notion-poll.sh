#!/usr/bin/env bash
# notion-poll.sh — Local Notion → eideticd sync, no Cloudflare Worker required.
#
# Cron-friendly:
#   */15 * * * * /path/to/notion-poll.sh \
#       --token "$NOTION_TOKEN" \
#       --db "$NOTION_DB_ID" \
#       --bridge "$BRIDGE_URL" \
#       --bridge-token "$BRIDGE_TOKEN"
#
# Reads every page in the configured Notion DB whose `last_edited_time` is
# newer than the on-disk checkpoint, renders each page to plain text, and
# POSTs it to the local daemon at `${BRIDGE_URL}/engrams`. Checkpoint advances
# only on a fully-successful batch (transient failures keep the window so the
# next tick retries).
#
# Dependencies: bash 4+, curl, jq.
#
# Privacy posture (ADR-020): the script reads Notion page content into memory,
# POSTs it to your local daemon over HTTPS, and discards. Only the checkpoint
# timestamp persists (in ${CHECKPOINT_DIR}). No content is logged.

set -euo pipefail

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

NOTION_API_BASE="https://api.notion.com/v1"
NOTION_API_VERSION="2022-06-28"
CHECKPOINT_DIR="${EIDETIC_NOTION_CHECKPOINT_DIR:-${HOME}/.eidetic/notion}"
POLL_PAGE_SIZE=100
POLL_MAX_PAGES=20
BLOCK_PAGE_SIZE=100
BLOCK_MAX_PAGES=10
ENGRAM_BODY_MAX_CHARS=32000
CURL_TIMEOUT_NOTION=15
CURL_TIMEOUT_BRIDGE=12

NOTION_TOKEN=""
NOTION_DB_ID=""
BRIDGE_URL=""
BRIDGE_TOKEN=""
DRY_RUN=0
VERBOSE=0

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

usage() {
  cat <<'EOF'
Usage: notion-poll.sh --token <NOTION_TOKEN> --db <DB_ID>
                      [--bridge <URL>] [--bridge-token <TOKEN>]
                      [--checkpoint-dir <DIR>] [--dry-run] [--verbose]

Required:
  --token         Notion internal integration token (starts with secret_/ntn_).
  --db            Notion database ID (32-char hex; dashes stripped).

Optional:
  --bridge        Bridge URL (default: env BRIDGE_URL or http://127.0.0.1:8787).
  --bridge-token  Bridge bearer token (default: env BRIDGE_TOKEN or contents
                  of ~/.eidetic/bridge-token).
  --checkpoint-dir  Where to store the last-edited timestamp (default:
                    ~/.eidetic/notion).
  --dry-run       Print engram payloads instead of POSTing them.
  --verbose       Log per-page progress to stderr.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token)          NOTION_TOKEN="$2"; shift 2 ;;
    --db)             NOTION_DB_ID="$2"; shift 2 ;;
    --bridge)         BRIDGE_URL="$2"; shift 2 ;;
    --bridge-token)   BRIDGE_TOKEN="$2"; shift 2 ;;
    --checkpoint-dir) CHECKPOINT_DIR="$2"; shift 2 ;;
    --dry-run)        DRY_RUN=1; shift ;;
    --verbose)        VERBOSE=1; shift ;;
    -h|--help)        usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

# Fill from env / disk fallbacks.
BRIDGE_URL="${BRIDGE_URL:-${EIDETIC_BRIDGE_URL:-http://127.0.0.1:8787}}"
if [[ -z "${BRIDGE_TOKEN}" ]]; then
  if [[ -n "${EIDETIC_BRIDGE_TOKEN:-}" ]]; then
    BRIDGE_TOKEN="${EIDETIC_BRIDGE_TOKEN}"
  elif [[ -r "${HOME}/.eidetic/bridge-token" ]]; then
    BRIDGE_TOKEN="$(cat "${HOME}/.eidetic/bridge-token")"
  fi
fi

# Normalise the DB ID — Notion URLs include dashes that the API does NOT.
NOTION_DB_ID="${NOTION_DB_ID//-/}"

# Validation.
if [[ -z "${NOTION_TOKEN}" || -z "${NOTION_DB_ID}" ]]; then
  echo "ERROR: --token and --db are required" >&2
  usage
  exit 2
fi
if [[ ! "${NOTION_DB_ID}" =~ ^[a-f0-9]{32}$ ]]; then
  echo "ERROR: --db must be a 32-character hex blob (got: ${NOTION_DB_ID})" >&2
  exit 2
fi
if [[ -z "${BRIDGE_TOKEN}" && "${DRY_RUN}" -eq 0 ]]; then
  echo "ERROR: bridge token unavailable. Pass --bridge-token, set EIDETIC_BRIDGE_TOKEN, or populate ~/.eidetic/bridge-token" >&2
  exit 2
fi

for cmd in curl jq; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "ERROR: ${cmd} is required but not on PATH" >&2
    exit 127
  fi
done

mkdir -p "${CHECKPOINT_DIR}"
CHECKPOINT_FILE="${CHECKPOINT_DIR}/${NOTION_DB_ID}.last_edited"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

log()  { echo "[notion-poll] $*" >&2; }
vlog() { [[ "${VERBOSE}" -eq 1 ]] && log "$*" || true; }

# ---------------------------------------------------------------------------
# Checkpoint I/O
# ---------------------------------------------------------------------------

read_checkpoint() {
  if [[ -r "${CHECKPOINT_FILE}" ]]; then
    cat "${CHECKPOINT_FILE}"
  else
    echo ""
  fi
}

# Atomic write — temp file + mv so a kill mid-write doesn't truncate the
# checkpoint and trigger a full DB re-sync next tick.
write_checkpoint() {
  local ts="$1"
  local tmp="${CHECKPOINT_FILE}.tmp.$$"
  printf '%s' "${ts}" > "${tmp}"
  mv "${tmp}" "${CHECKPOINT_FILE}"
}

# ---------------------------------------------------------------------------
# Notion API calls
# ---------------------------------------------------------------------------

notion_curl() {
  curl --silent --show-error --fail-with-body \
       --max-time "${CURL_TIMEOUT_NOTION}" \
       -H "Authorization: Bearer ${NOTION_TOKEN}" \
       -H "Notion-Version: ${NOTION_API_VERSION}" \
       -H "Content-Type: application/json" \
       "$@"
}

# Query the DB for pages with last_edited_time > checkpoint. Paginated.
# Emits one JSON page-object per stdout line.
query_db_pages() {
  local checkpoint="$1"
  local cursor=""
  local page_idx=0
  while [[ "${page_idx}" -lt "${POLL_MAX_PAGES}" ]]; do
    local body
    body=$(jq -nc \
      --argjson page_size "${POLL_PAGE_SIZE}" \
      --arg checkpoint "${checkpoint}" \
      --arg cursor "${cursor}" \
      '
      {
        page_size: $page_size,
        sorts: [{ timestamp: "last_edited_time", direction: "ascending" }]
      }
      + (if $cursor == "" then {} else { start_cursor: $cursor } end)
      + (if $checkpoint == "" then {} else
          { filter: { timestamp: "last_edited_time",
                      last_edited_time: { after: $checkpoint } } }
        end)
      ')
    local resp
    if ! resp=$(notion_curl -X POST \
        "${NOTION_API_BASE}/databases/${NOTION_DB_ID}/query" \
        --data "${body}"); then
      log "ERROR: databases.query failed; aborting batch"
      return 1
    fi
    # Emit page rows.
    echo "${resp}" | jq -c '.results[]'
    local has_more next_cursor
    has_more=$(echo "${resp}" | jq -r '.has_more // false')
    next_cursor=$(echo "${resp}" | jq -r '.next_cursor // ""')
    if [[ "${has_more}" != "true" || -z "${next_cursor}" ]]; then
      break
    fi
    cursor="${next_cursor}"
    page_idx=$((page_idx + 1))
  done
}

# Fetch block children for a page; emits one block JSON per line.
fetch_blocks() {
  local block_id="$1"
  local cursor=""
  local page_idx=0
  while [[ "${page_idx}" -lt "${BLOCK_MAX_PAGES}" ]]; do
    local url="${NOTION_API_BASE}/blocks/${block_id}/children?page_size=${BLOCK_PAGE_SIZE}"
    if [[ -n "${cursor}" ]]; then
      url="${url}&start_cursor=${cursor}"
    fi
    local resp
    if ! resp=$(notion_curl "${url}"); then
      log "WARN: block fetch for ${block_id} failed; returning partial"
      return 0
    fi
    echo "${resp}" | jq -c '.results[]'
    local has_more next_cursor
    has_more=$(echo "${resp}" | jq -r '.has_more // false')
    next_cursor=$(echo "${resp}" | jq -r '.next_cursor // ""')
    if [[ "${has_more}" != "true" || -z "${next_cursor}" ]]; then
      break
    fi
    cursor="${next_cursor}"
    page_idx=$((page_idx + 1))
  done
}

# Render a block JSON (stdin) to a single line of plain text.
block_to_text() {
  jq -r '
    . as $b |
    ($b.type) as $t |
    ($b[$t]) as $n |
    if $n == null then empty
    else
      ($n.rich_text // [] | map(.plain_text // "") | join("")) as $text |
      if   $t == "paragraph"           then $text
      elif $t == "quote"               then $text
      elif $t == "callout"             then $text
      elif $t == "heading_1"           then (if $text == "" then "" else "# "   + $text end)
      elif $t == "heading_2"           then (if $text == "" then "" else "## "  + $text end)
      elif $t == "heading_3"           then (if $text == "" then "" else "### " + $text end)
      elif $t == "bulleted_list_item"  then (if $text == "" then "" else "- "   + $text end)
      elif $t == "numbered_list_item"  then (if $text == "" then "" else "1. "  + $text end)
      elif $t == "to_do"               then
        (if $text == "" then ""
         else (if ($n.checked // false) then "- [x] " else "- [ ] " end) + $text end)
      elif $t == "toggle"              then $text
      elif $t == "code"                then
        (if $text == "" then ""
         else "```" + ($n.language // "") + "\n" + $text + "\n```" end)
      elif $t == "divider"             then "---"
      elif ($t == "bookmark" or $t == "embed" or $t == "link_preview")
                                       then ($n.url // "")
      else ""
      end
    end
  '
}

# Render the full page body by walking all top-level blocks. Output: plain text.
render_page_body() {
  local page_id="$1"
  local out=""
  while IFS= read -r block; do
    [[ -z "${block}" ]] && continue
    local line
    line=$(echo "${block}" | block_to_text)
    if [[ -n "${line}" ]]; then
      if [[ -z "${out}" ]]; then
        out="${line}"
      else
        out="${out}"$'\n'"${line}"
      fi
    fi
  done < <(fetch_blocks "${page_id}")
  printf '%s' "${out}"
}

# Extract the title from a page-object's properties (whichever has type=title).
extract_title() {
  jq -r '
    (.properties // {}) as $props |
    [
      $props | to_entries[] |
      select(.value.type == "title") |
      (.value.title // [] | map(.plain_text // "") | join(""))
    ] | map(select(. != "")) | first // "(untitled)"
  '
}

# ---------------------------------------------------------------------------
# Bridge POST
# ---------------------------------------------------------------------------

post_engram() {
  local engram_json="$1"
  if [[ "${DRY_RUN}" -eq 1 ]]; then
    echo "${engram_json}"
    return 0
  fi
  local url="${BRIDGE_URL%/}/engrams"
  local http_status
  http_status=$(curl --silent --show-error \
       --max-time "${CURL_TIMEOUT_BRIDGE}" \
       --output /tmp/notion-poll.bridge.$$ \
       --write-out '%{http_code}' \
       -X POST "${url}" \
       -H "Authorization: Bearer ${BRIDGE_TOKEN}" \
       -H "Content-Type: application/json" \
       --data "${engram_json}" || echo "000")
  local body
  body=$(cat /tmp/notion-poll.bridge.$$ 2>/dev/null || true)
  rm -f /tmp/notion-poll.bridge.$$
  if [[ ! "${http_status}" =~ ^2 ]]; then
    log "ERROR: bridge POST HTTP ${http_status}: ${body:0:240}"
    return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# Main poll
# ---------------------------------------------------------------------------

main() {
  local checkpoint
  checkpoint=$(read_checkpoint)
  vlog "checkpoint = ${checkpoint:-<empty>}"

  local scanned=0
  local posted=0
  local failed=0
  local newest_seen="${checkpoint}"

  while IFS= read -r page; do
    [[ -z "${page}" ]] && continue
    scanned=$((scanned + 1))
    local page_id last_edited title body
    page_id=$(echo "${page}" | jq -r '.id // ""')
    last_edited=$(echo "${page}" | jq -r '.last_edited_time // ""')
    if [[ -z "${page_id}" ]]; then
      vlog "skipping page with no id"
      continue
    fi
    title=$(echo "${page}" | extract_title)
    vlog "page ${page_id} (${title}) last_edited=${last_edited}"

    body=$(render_page_body "${page_id}")
    # Cap body length so a runaway page doesn't blow up the bridge POST.
    if [[ "${#body}" -gt "${ENGRAM_BODY_MAX_CHARS}" ]]; then
      body="${body:0:${ENGRAM_BODY_MAX_CHARS}}"
      vlog "truncated body for ${page_id}"
    fi

    local notion_url
    notion_url=$(echo "${page}" | jq -r '.url // ""')

    # Build engram JSON via jq for safe string escaping (handles quotes, newlines).
    local engram_json
    engram_json=$(jq -nc \
      --arg title "${title}" \
      --arg body "${body}" \
      --arg page_id "${page_id}" \
      --arg db_id "${NOTION_DB_ID}" \
      --arg url "${notion_url}" \
      --arg last_edited "${last_edited}" \
      '{
         surface: "notion",
         title: $title,
         payload: $body,
         meta: {
           notion_page_id: $page_id,
           notion_db_id: $db_id,
           notion_url: $url,
           last_edited_time: $last_edited
         }
       }')

    if post_engram "${engram_json}"; then
      posted=$((posted + 1))
      if [[ -n "${last_edited}" && "${last_edited}" > "${newest_seen}" ]]; then
        newest_seen="${last_edited}"
      fi
    else
      failed=$((failed + 1))
    fi
  done < <(query_db_pages "${checkpoint}")

  # Advance only if at least one page succeeded AND the timestamp moved.
  if [[ "${posted}" -gt 0 && -n "${newest_seen}" && "${newest_seen}" > "${checkpoint}" ]]; then
    write_checkpoint "${newest_seen}"
  fi

  log "scanned=${scanned} posted=${posted} failed=${failed} checkpoint=${newest_seen:-<empty>}"
}

main
