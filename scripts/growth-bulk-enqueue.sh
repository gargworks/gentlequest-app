#!/usr/bin/env bash
#
# growth-bulk-enqueue.sh
#
# Walks docs/posts/queue/, parses YAML frontmatter (channel, target) from each
# day-NN-*.md file, reads the post body, and POSTs to the growth-scheduler's
# /queue endpoint.
#
# Idempotent: skips any post whose .posted sentinel already exists in
# docs/posts/queue/.posted/.
#
# Required env:
#   WORKER_URL     base URL of the growth-scheduler worker (no trailing slash)
#   ADMIN_SECRET   bearer token for the worker's admin auth
#
# Optional env:
#   QUEUE_DIR      override queue path (default: <repo>/docs/posts/queue)
#   DRY_RUN        any non-empty value: print payloads, do not POST
#
# Example:
#   WORKER_URL=https://growth.eidetic.works \
#   ADMIN_SECRET=xxx \
#   ./scripts/growth-bulk-enqueue.sh

set -euo pipefail

# ----- config -----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
QUEUE_DIR="${QUEUE_DIR:-${REPO_ROOT}/docs/posts/queue}"
SENTINEL_DIR="${QUEUE_DIR}/.posted"

: "${WORKER_URL:?WORKER_URL is required (e.g. https://growth.eidetic.works)}"
: "${ADMIN_SECRET:?ADMIN_SECRET is required}"

# Strip any trailing slash on WORKER_URL.
WORKER_URL="${WORKER_URL%/}"

if [ ! -d "${QUEUE_DIR}" ]; then
  echo "queue dir not found: ${QUEUE_DIR}" >&2
  exit 1
fi

mkdir -p "${SENTINEL_DIR}"

# ----- helpers -----

# parse_frontmatter_field FILE KEY
# Echoes the value of the YAML key in the file's frontmatter (between the
# first two `---` markers). Empty if missing. Portable across BSD/GNU awk.
parse_frontmatter_field() {
  local file="$1"
  local key="$2"
  awk -v k="${key}" '
    BEGIN { in_fm=0 }
    /^---$/ {
      if (in_fm) { exit } else { in_fm=1; next }
    }
    in_fm {
      prefix = k ":"
      n = length(prefix)
      if (substr($0, 1, n) == prefix) {
        v = substr($0, n+1)
        sub(/^[ \t]+/, "", v); sub(/[ \t]+$/, "", v)
        sub(/^"/, "", v); sub(/"$/, "", v)
        sub(/^'\''/, "", v); sub(/'\''$/, "", v)
        print v
        exit
      }
    }
  ' "${file}"
}

# parse_body FILE
# Echoes the body content (everything after the second `---`), stripped of
# surrounding blank lines.
parse_body() {
  local file="$1"
  awk '
    BEGIN { fm_count=0 }
    /^---$/ { fm_count++; next }
    fm_count >= 2 { print }
  ' "${file}" | awk '
    # collapse leading blank lines
    NR==1 && /^[ \t]*$/ { next }
    { buf[NR]=$0; if ($0 !~ /^[ \t]*$/) last=NR }
    END { for (i=1; i<=last; i++) print buf[i] }
  '
}

# json_escape STRING
# Emits a JSON string literal (without surrounding quotes) for the input.
json_escape() {
  python3 -c 'import json,sys; sys.stdout.write(json.dumps(sys.stdin.read())[1:-1])'
}

# ----- main loop -----

shopt -s nullglob
files=( "${QUEUE_DIR}"/day-*.md )
shopt -u nullglob

if [ "${#files[@]}" -eq 0 ]; then
  echo "no day-*.md files found in ${QUEUE_DIR}" >&2
  exit 1
fi

posted=0
skipped=0
failed=0

for file in "${files[@]}"; do
  base="$(basename "${file}" .md)"
  sentinel="${SENTINEL_DIR}/${base}.posted"

  if [ -f "${sentinel}" ]; then
    printf "skip   %-44s (already posted: %s)\n" "${base}" "$(cat "${sentinel}")"
    skipped=$((skipped + 1))
    continue
  fi

  channel="$(parse_frontmatter_field "${file}" channel)"
  target="$(parse_frontmatter_field "${file}"  target)"
  topic="$(parse_frontmatter_field   "${file}" topic)"
  day="$(parse_frontmatter_field     "${file}" day)"
  body="$(parse_body "${file}")"

  if [ -z "${channel}" ] || [ -z "${target}" ] || [ -z "${body}" ]; then
    printf "ERROR  %-44s missing channel/target/body\n" "${base}" >&2
    failed=$((failed + 1))
    continue
  fi

  # Build JSON payload.
  body_escaped="$(printf '%s' "${body}" | json_escape)"
  topic_escaped="$(printf '%s' "${topic}" | json_escape)"
  source_file_escaped="$(printf '%s' "${base}" | json_escape)"
  payload=$(cat <<EOF
{"channel":"${channel}","target":"${target}","body":"${body_escaped}","topic":"${topic_escaped}","source_file":"${source_file_escaped}","day":${day:-0}}
EOF
)

  if [ -n "${DRY_RUN:-}" ]; then
    printf "DRY    %-44s channel=%s target=%s bytes=%d\n" \
      "${base}" "${channel}" "${target}" "${#body}"
    continue
  fi

  http_response="$(
    curl --silent --show-error --fail-with-body \
         --write-out '\n%{http_code}' \
         --max-time 30 \
         -X POST "${WORKER_URL}/queue" \
         -H "Authorization: Bearer ${ADMIN_SECRET}" \
         -H "Content-Type: application/json" \
         --data "${payload}" \
      || true
  )"

  status_code="${http_response##*$'\n'}"
  body_response="${http_response%$'\n'*}"

  if [ "${status_code}" = "200" ] || [ "${status_code}" = "201" ] || [ "${status_code}" = "202" ]; then
    queued_id="$(printf '%s' "${body_response}" \
      | python3 -c 'import sys,json
try:
    d=json.loads(sys.stdin.read()); print(d.get("id") or d.get("queue_id") or d.get("uuid") or "")
except Exception:
    print("")' || true)"
    printf "OK     %-44s id=%s status=%s\n" "${base}" "${queued_id:-?}" "${status_code}"
    # Write sentinel: ISO-8601 timestamp + queued id.
    printf '%s id=%s status=%s\n' \
      "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${queued_id:-?}" "${status_code}" \
      > "${sentinel}"
    posted=$((posted + 1))
  else
    printf "FAIL   %-44s status=%s body=%s\n" "${base}" "${status_code}" "${body_response}" >&2
    failed=$((failed + 1))
  fi
done

echo
printf "summary: posted=%d skipped=%d failed=%d total=%d\n" \
  "${posted}" "${skipped}" "${failed}" "${#files[@]}"

if [ "${failed}" -gt 0 ]; then
  exit 2
fi
