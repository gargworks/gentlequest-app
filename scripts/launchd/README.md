# launchd plists for Nucleus

One-time activation commands. Each plist is idempotent — `unload` then `load` to refresh.

## com.nucleus.cc_jsonl_mirror.plist

Extracts last-turn METADATA (not full transcripts) from Mac CC session JSONLs every 30s and writes a single compact `.brain/cc_transcripts/_status.json` for Cowork to tail.

**Footprint:** ~500 bytes per active session, single file overwritten each run. CC jsonls are 10-30MB+ each — full mirror would be wasteful for the watcher use case.

```bash
# Install (copy to LaunchAgents)
cp /Users/lokeshgarg/ai-mvp-backend/scripts/launchd/com.nucleus.cc_jsonl_mirror.plist \
   ~/Library/LaunchAgents/com.nucleus.cc_jsonl_mirror.plist

# Load + start
launchctl load ~/Library/LaunchAgents/com.nucleus.cc_jsonl_mirror.plist

# Verify (look for the label, second column should be a PID once first run kicks off)
launchctl list | grep cc_jsonl_mirror

# Inspect what Cowork now sees
cat /Users/lokeshgarg/ai-mvp-backend/.brain/cc_transcripts/_status.json | python3 -m json.tool

# Tail logs
tail -f /Users/lokeshgarg/ai-mvp-backend/.brain/log/cc_jsonl_mirror.out.log

# Pause
launchctl unload ~/Library/LaunchAgents/com.nucleus.cc_jsonl_mirror.plist
```

## What's in `_status.json`

Three tiers, scaled by freshness so the file stays compact even with 1000+ historical sessions:

```json
{
  "generated_at_iso": "2026-04-21T08:30:00Z",
  "active_window_hours": 2.0,
  "recent_window_hours": 24.0,
  "active_count": 1,
  "recent_count": 4,
  "stale_count": 988,
  "stale_total_bytes": 3214567890,
  "stale_oldest_age_seconds": 5184000,
  "stale_newest_age_seconds": 86401,
  "total_count": 993,
  "sessions": {
    "<session-uuid>": {
      "size_bytes": 29345782,
      "mtime_epoch": 1745234567.0,
      "age_seconds": 47,
      "in_active_window": true,
      "last_turn_type": "assistant",
      "last_turn_ts": "2026-04-21T08:29:13Z",
      "last_tool_name": "Bash",
      "is_waiting_on_tool": true,
      "heuristic_state": "waiting_on_tool"
    }
  },
  "recent_sessions": {
    "<session-uuid>": {
      "size_bytes": 12345678,
      "mtime_epoch": 1745230000.0,
      "age_seconds": 7200
    }
  }
}
```

Tiers:
- **active** (`age < active_window_hours`, default 2h) — full metadata + last-turn parse. This is what cc-idle-watcher reads to decide stall-vs-working.
- **recent** (`active_window_hours <= age < recent_window_hours`, default 24h) — minimal entry (size/mtime/age only). No tail parse, saves compute.
- **stale** (`age >= recent_window_hours`) — aggregated into `stale_count` + `stale_total_bytes` + age min/max. Zero per-session footprint.

`heuristic_state` (active tier only) is what Cowork's watcher reads to refine `[cc-idle-watch]` Telegram alerts:
- `waiting_on_tool` + silent N min → "stuck on `<tool_name>`, likely awaiting permission"
- `assistant_replied` + silent N min → "quiescent, waiting for your next prompt"
- `user_prompted` + silent N min → "CC mid-thinking on `<turn_ts>`, may be a long task or hung model"

Typical size: <5KB for a repo with ~1000 historical sessions + a handful active (vs 187KB before the tiered filter).

## com.nucleus.auto_awake_daemon.plist

Tier 1 headless proxy worker (Sub-slice B). Polls `.brain/relay/<bucket>/*.json` every 30s for unread `[DIRECTIVE]` / `[DIRECTIVE-ON-WAKE]` envelopes and fires the matching per-provider CLI as a fire-and-forget subprocess. Dedups by `relay_id` in `.brain/state/auto_awake_dispatched.json` so each envelope dispatches at most once.

**Provider wiring is opt-in via env vars** — missing env = quiet skip (`no-cli-configured` recorded in dedup state). Add CLI envs to the plist's `EnvironmentVariables` block to wake a provider:

```xml
<key>NUCLEUS_AWAKE_CMD_ANTHROPIC_CLAUDE_CODE</key>
<string>claude -p</string>
<key>NUCLEUS_AWAKE_CMD_GOOGLE_GEMINI</key>
<string>gemini -p</string>
```

Provider tokens come from `mcp-server-nucleus/src/mcp_server_nucleus/runtime/providers.yaml` (uppercased, non-alphanumerics → `_`).

```bash
# Install (copy to LaunchAgents)
cp /Users/lokeshgarg/ai-mvp-backend/scripts/launchd/com.nucleus.auto_awake_daemon.plist \
   ~/Library/LaunchAgents/com.nucleus.auto_awake_daemon.plist

# Load + start
launchctl load ~/Library/LaunchAgents/com.nucleus.auto_awake_daemon.plist

# Verify (look for the label, second column should be a PID once first run kicks off)
launchctl list | grep auto_awake_daemon

# Inspect dedup state
cat /Users/lokeshgarg/ai-mvp-backend/.brain/state/auto_awake_dispatched.json | python3 -m json.tool

# Tail logs
tail -f /Users/lokeshgarg/ai-mvp-backend/.brain/log/auto_awake_daemon.out.log

# Pause
launchctl unload ~/Library/LaunchAgents/com.nucleus.auto_awake_daemon.plist
```

Ad-hoc test (single pass, no daemon):

```bash
bash /Users/lokeshgarg/ai-mvp-backend/scripts/auto_awake_daemon.sh
# expected: "auto-awake dispatched=N"
```

### Gemini CLI (Tier 1 viable as of 2026-04-25)

`gemini -p` accepts a prompt argument and reads stdin appended to the prompt — verified against the installed `gemini` binary. Wiring it is one env var:

```xml
<key>NUCLEUS_AWAKE_CMD_GOOGLE_GEMINI</key>
<string>gemini -p</string>
```

The daemon pipes the relay envelope JSON on stdin; Gemini reads it as appended context.

### Cut-line

Tier 1 covers headless CLI providers only. GUI providers (Cursor, Windsurf, Antigravity) stay on the Tier 4 doc-interrupt fallback — adding them would mean wiring a UI deep-link / `osascript` shim per provider, which is deferred until the 3rd CLI provider lands (per `feedback_compounding_shape.md` ADR rule).
