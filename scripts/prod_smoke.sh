#!/usr/bin/env bash
set -u -o pipefail

BASE_URL="${BASE_URL:-https://gentlequest.onrender.com}"
CLEANUP=false
SESSION_ID="${SMOKE_SESSION_ID:-smoke-$(date +%s)-$}"
RESP_FILE="${SMOKE_RESP_FILE:-/tmp/gq_prod_smoke_resp.json}"
LATENCIES=()
PASSED=0
FAILED=0
TOTAL=0
JOURNAL_ID=""
PUSH_TOKEN="smoke-token"

for arg in "$@"; do
  case "$arg" in
    --cleanup) CLEANUP=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 2 ;;
  esac
done

run_step() {
  local name="$1"
  local method="$2"
  local path="$3"
  local body="${4:-}"
  local url="${BASE_URL}${path}"
  local output
  local status
  local latency

  TOTAL=$((TOTAL + 1))
  if [[ -n "$body" ]]; then
    output=$(curl -s -o "$RESP_FILE" -w '%{http_code} %{time_total}' -X "$method" "$url" \
      -H "X-Session-ID: $SESSION_ID" \
      -H 'Content-Type: application/json' \
      -d "$body")
  else
    output=$(curl -s -o "$RESP_FILE" -w '%{http_code} %{time_total}' -X "$method" "$url" \
      -H "X-Session-ID: $SESSION_ID")
  fi

  status="${output%% *}"
  latency="${output##* }"
  LATENCIES+=("$latency")

  if [[ "$status" =~ ^2[0-9][0-9]$ ]]; then
    PASSED=$((PASSED + 1))
    printf 'PASS %-42s %s %ss\n' "$name" "$status" "$latency"
  else
    FAILED=$((FAILED + 1))
    printf 'FAIL %-42s %s %ss\n' "$name" "$status" "$latency"
    sed 's/^/  response: /' "$RESP_FILE" 2>/dev/null || true
  fi
}

extract_json_field() {
  local field="$1"
  python3 - "$field" "$RESP_FILE" <<'PY'
import json
import sys
field, path = sys.argv[1:]
try:
    with open(path) as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        value = data.get(field, "")
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        value = data[0].get(field, "")
    else:
        value = ""
    print(value or "")
except Exception:
    print("")
PY
}

percentile() {
  local pct="$1"
  python3 - "$pct" "${LATENCIES[@]}" <<'PY'
import math
import sys
pct = float(sys.argv[1])
values = sorted(float(v) for v in sys.argv[2:])
if not values:
    print("0.000")
else:
    idx = min(len(values) - 1, max(0, math.ceil((pct / 100.0) * len(values)) - 1))
    print(f"{values[idx]:.3f}")
PY
}

echo "GentleQuest production smoke suite"
echo "BASE_URL=$BASE_URL"
echo "SESSION_ID=$SESSION_ID"
echo

run_step "health" "GET" "/api/health"
run_step "session" "POST" "/api/session"
run_step "mood create" "POST" "/api/mood_entry" '{"moodLevel":3,"contextChips":["Work","Sleep"]}'
run_step "mood history" "GET" "/api/mood_history"
run_step "journal create" "POST" "/api/journal" '{"body":"smoke test"}'
JOURNAL_ID="$(extract_json_field id)"
run_step "journal list" "GET" "/api/journal"
if [[ -n "$JOURNAL_ID" ]]; then
  run_step "journal update" "PATCH" "/api/journal/${JOURNAL_ID}" '{"body":"updated"}'
  run_step "journal delete" "DELETE" "/api/journal/${JOURNAL_ID}"
else
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
  echo "FAIL journal update/delete dependency missing journal id"
fi
run_step "user get" "GET" "/api/user"
run_step "user export" "POST" "/api/user/export"
run_step "anonymity enable" "POST" "/api/user/anonymity" '{"enabled":true}'
run_step "notification prefs update" "POST" "/api/user/notification_prefs" '{"daily_checkin_enabled":true}'
run_step "notification prefs get" "GET" "/api/user/notification_prefs"
run_step "resource favorite" "POST" "/api/user/resources/favorite" '{"resource_id":"box-breathing","favorite":true}'
run_step "resource favorites" "GET" "/api/user/resources/favorites"
run_step "resource opened" "POST" "/api/user/resources/opened" '{"resource_id":"box-breathing"}'
run_step "resource recents" "GET" "/api/user/resources/recents?limit=3"
run_step "push token create" "POST" "/api/user/push-tokens" "{\"token\":\"${PUSH_TOKEN}\",\"platform\":\"ios\"}"
run_step "push token list" "GET" "/api/user/push-tokens"
run_step "push token delete" "DELETE" "/api/user/push-tokens/${PUSH_TOKEN}"

if [[ "$CLEANUP" == true ]]; then
  run_step "cleanup user delete" "DELETE" "/api/user"
fi

P50="$(percentile 50)"
P95="$(percentile 95)"

echo
echo "Summary"
printf 'total=%s passed=%s failed=%s p50=%ss p95=%ss\n' "$TOTAL" "$PASSED" "$FAILED" "$P50" "$P95"

if [[ "$FAILED" -eq 0 ]]; then
  exit 0
fi
exit 1
