#!/usr/bin/env bash
# Deploy the current main to Render, wait for it, and SMOKE IT.
#
# Why this exists (2026-09-03): the GitLab project has ZERO webhooks, so
# nothing tells Render a push happened. Render's dashboard says
# `autoDeploy: yes`, which is why the setting looks healthy while no deploy
# ever fires — the setting is real, the delivery mechanism is missing. Until a
# webhook or deploy hook is added in the Render dashboard, every backend
# change must be deployed by hand. This makes that ~10 seconds.
#
# It deliberately does NOT stop at "live". A live status means Render started
# the new container, not that the change works; this session shipped a fix
# whose whole point was that a green signal was being read off the wrong
# object. So the last thing this script does is exercise the real endpoints.
#
# Usage:  scripts/deploy_render.sh [commit-sha]     (default: current HEAD)
set -euo pipefail

SERVICE="srv-d2r3i1fdiees73dqtov0"
BASE="https://app.gentlequest.app"
SHA="${1:-$(git rev-parse HEAD)}"

KEY=$(python3 -c "import yaml,os;print(yaml.safe_load(open(os.path.expanduser('~/.render/cli.yaml')))['api']['key'])")
EXP=$(python3 -c "import yaml,os;print(yaml.safe_load(open(os.path.expanduser('~/.render/cli.yaml')))['api']['expires_at'])")
NOW=$(date +%s)
LEFT=$(( (EXP - NOW) / 86400 ))
if [ "$LEFT" -lt 0 ]; then
  echo "Render CLI token EXPIRED. Run: render login" >&2
  exit 1
elif [ "$LEFT" -lt 7 ]; then
  # The token in ~/.render/cli.yaml is a CLI SESSION token, not a long-lived
  # API key. It expires quietly, and the first symptom is a 401 during an
  # urgent deploy. Say so early.
  echo "WARNING: Render token expires in ${LEFT} day(s). Run 'render login' soon." >&2
fi

echo "==> deploying ${SHA:0:8} to $SERVICE"
DEPLOY_ID=$(curl -fsS -X POST \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d "{\"commitId\":\"$SHA\"}" \
  "https://api.render.com/v1/services/$SERVICE/deploys" \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
echo "    deploy $DEPLOY_ID"

for _ in $(seq 1 60); do
  STATUS=$(curl -fsS -H "Authorization: Bearer $KEY" \
    "https://api.render.com/v1/services/$SERVICE/deploys/$DEPLOY_ID" \
    | python3 -c "import json,sys;print(json.load(sys.stdin).get('status'))")
  echo "    $(date +%H:%M:%S) $STATUS"
  case "$STATUS" in
    live) break ;;
    build_failed|update_failed|canceled|pre_deploy_failed)
      echo "DEPLOY FAILED: $STATUS" >&2; exit 1 ;;
  esac
  sleep 15
done
[ "$STATUS" = "live" ] || { echo "timed out waiting for live (last: $STATUS)" >&2; exit 1; }

echo "==> smoke: health"
curl -fsS -o /dev/null -w "    health %{http_code}\n" "$BASE/api/health"

# Read the counter BEFORE the smoke, so the assertion can be about the DELTA.
# An absolute check cannot tell a rejected bot from a counted one.
read_landing() {
  curl -fsS "$BASE/api/metrics/funnel?days=1" \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['counts']['landing_sessions'])"
}
BEFORE=$(read_landing)

echo "==> smoke: session grouping (3 events, one session id -> must add exactly 1)"
SID=$(python3 -c "import uuid;print(uuid.uuid4())")
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
for _ in 1 2 3; do
  curl -fsS -o /dev/null -X POST "$BASE/api/analytics/log" \
    -H "Content-Type: application/json" -H "X-Analytics-Consent: true" \
    -H "X-Session-ID: $SID" -H "User-Agent: $UA" \
    -d '{"event_type":"cta_impression","metadata":{"cta_id":"deploy_smoke"}}'
done

echo "==> smoke: bot rejection (a bot claiming to be human must NOT count)"
curl -fsS -o /dev/null -X POST "$BASE/api/analytics/log" \
  -H "Content-Type: application/json" -H "X-Analytics-Consent: true" \
  -H "X-Session-ID: $(python3 -c 'import uuid;print(uuid.uuid4())')" \
  -H "User-Agent: Mozilla/5.0 (compatible; Googlebot/2.1)" \
  -d '{"event_type":"cta_impression","metadata":{"cta_id":"deploy_smoke","_ua_class":"human"}}'

AFTER=$(read_landing)
DELTA=$(( AFTER - BEFORE ))
echo "    landing_sessions ${BEFORE} -> ${AFTER} (delta ${DELTA})"

# The delta is the whole test, and it is two assertions in one number.
#
# Corrected 2026-09-03 after a cross-vendor audit: this block used to assert
# only `landing_sessions >= 1` and then print "the forged bot was not counted".
# That sentence was never checked. If the bot HAD been counted the number would
# simply have been larger and the script would still have printed it and exited
# 0 — a guard whose message claimed more than its assertion, which is the exact
# defect the deploy it guards was written to fix.
#
#   delta 1 -> the 3 human events grouped into ONE session, and the bot was
#              rejected. Both properties, one number.
#   delta 0 -> session grouping is broken (or the events never landed).
#   delta 2 -> the forged bot was counted as human. THIS is the regression the
#              bot filter exists to prevent.
if [ "$DELTA" -ne 1 ]; then
  echo "SMOKE FAILED: expected exactly +1 landing session, got ${DELTA}." >&2
  if [ "$DELTA" -ge 2 ]; then
    echo "  A delta of 2+ means the forged bot was counted as human." >&2
  else
    echo "  A delta of 0 means the 3 events did not group into a session." >&2
  fi
  exit 1
fi
echo "    OK — 3 events grouped into 1 session AND the forged bot was rejected."

echo "==> done: ${SHA:0:8} live and smoke-verified"
