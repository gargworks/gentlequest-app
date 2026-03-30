# Smart Drain & First User Alert - Quick Guide

## What You Get

**Smart Drain Script** - Fully automatic, zero-maintenance:
- If Docker Desktop is **not running** → starts it, waits for ready, drains, stops it
- If Docker Desktop is **running** → just drains, leaves it running
- If telemetry containers are down → starts them, drains, stops them
- If telemetry containers are up → just drains, leaves them running
- Runs every 12 hours via cron
- **No manual intervention needed** - works whether Docker is on or off

**First User Alert** - Get notified when real users arrive:
- Detects telemetry from non-your Python versions or platforms
- Creates alert file with user details
- Shows macOS notification (if available)
- Only alerts once (first user)

---

## Setup (One-Time)

```bash
cd /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus

# Set up the cron job (runs every 12 hours)
npm run telemetry:setup-cron
```

This will:
- Remove old telemetry:drain cron (if exists)
- Add smart drain cron (runs at 00:00 and 12:00 daily)
- Configure first-user detection

---

## Manual Commands

```bash
# Test smart drain manually
npm run telemetry:smart-drain

# Or with full path
npm --prefix /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus run telemetry:smart-drain
```

---

## How It Works

### Smart Drain Logic

1. **Check Docker Desktop** - Is it running?
   - If **not running** → Start Docker Desktop, wait up to 60s for daemon to be ready
   - If **running** → Continue
2. **Check telemetry containers** - Are they already up?
   - If **down** → Start containers
   - If **up** → Continue
3. **Drain spans** - Pull from Upstash → local collector
4. **Check for first user** - Scan traces for external telemetry
5. **Clean up** - Only stop what we started:
   - If we started containers → Stop containers
   - If we started Docker Desktop → Quit Docker Desktop
   - If they were already running → Leave them running

### First User Detection

Filters out your telemetry by checking:
- Python versions: `3.9.6`, `3.11.14`, `3.14.2` (yours)
- Platform: `darwin` (yours)

Any span with different Python version OR different platform = external user.

When detected:
- Creates `.telemetry/first-user-detected` file
- Shows macOS notification
- Logs to `.telemetry/smart-drain.log`
- Only alerts once (won't spam)

---

## Logs & Monitoring

```bash
# View smart drain log
tail -f .telemetry/smart-drain.log

# Check if first user detected
cat .telemetry/first-user-detected

# View all traces
cat .telemetry/traces.jsonl | jq .

# Filter for external users only
cat .telemetry/traces.jsonl | grep -v "3.9.6\|3.11.14\|3.14.2"
```

---

## Current Setup Summary

**Your telemetry:** OFF (via `npm run telemetry:off`)
- Saves ~10K Upstash commands/day
- Keeps 430K+ headroom for real users

**Smart drain:** Every 12 hours
- Minimal resource usage (containers only up when draining)
- Automatic first-user detection
- Logs everything to `.telemetry/smart-drain.log`

**Upstash usage:** 81K / 500K (16%)
- Most is from old drain polling (now replaced)
- With your telemetry OFF + smart drain, usage will drop significantly

---

## Cron Schedule

```
0 */12 * * * bash /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/scripts/smart-drain.sh
```

Runs at:
- 00:00 (midnight)
- 12:00 (noon)

To verify: `crontab -l`

---

## What Happens When First User Arrives

You'll see:
1. **macOS notification** - "🎉 First Nucleus User! Python X.X.X on platform"
2. **Alert file** - `.telemetry/first-user-detected` with details
3. **Log entry** - In `.telemetry/smart-drain.log`

Example alert:
```
🎉 FIRST EXTERNAL USER DETECTED!

Timestamp: 2026-03-15 20:30:45
Python Version: 3.10.12
Platform: linux
Command: nucleus.cli.tasks.list

This is NOT your telemetry (you use Python 3.9.6 3.11.14 3.14.2 on darwin).

Check traces.jsonl for more details:
  cat /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/.telemetry/traces.jsonl | grep -v "3.9.6\|3.11.14\|3.14.2"

Congratulations! 🚀
```

---

## Files Created

- `scripts/smart-drain.sh` - Main drain script
- `scripts/first-user-alert.sh` - Detection script
- `scripts/setup-smart-drain-cron.sh` - Cron installer
- `.telemetry/smart-drain.log` - Execution log
- `.telemetry/first-user-detected` - Alert file (created when first user arrives)

---

## Troubleshooting

**Cron not running?**
```bash
crontab -l  # Verify it's there
tail -f .telemetry/smart-drain.log  # Check logs
```

**Want to test first-user detection?**
```bash
# Manually run the alert script
bash scripts/first-user-alert.sh
```

**Want to reset first-user alert?**
```bash
rm .telemetry/first-user-detected
```

**Want to change schedule?**
```bash
crontab -e
# Change: 0 */12 * * * to whatever you want
# Examples:
#   0 */6 * * *   - Every 6 hours
#   0 0 * * *     - Daily at midnight
#   0 0,12 * * *  - Twice daily (midnight and noon)
```

---

## Next Steps

1. ✅ Your telemetry is OFF (saving quota)
2. ✅ Smart drain is set up (every 12 hours)
3. ✅ First-user alert is active
4. ⏳ Wait for first external user (monitor via alert)
5. 🚀 When alerted, check `.telemetry/first-user-detected` for details

**You're all set!** The system will automatically detect and notify you when the first real user arrives.
