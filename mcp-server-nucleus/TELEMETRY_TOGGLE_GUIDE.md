# Telemetry Toggle - Quick Reference

## Super Simple Commands

```bash
# Turn OFF your telemetry (save quota for real users)
npm run telemetry:off

# Turn ON your telemetry (dogfood your own product)
npm run telemetry:on

# Check current status
npm run telemetry:status

# Quick toggle (switch between on/off)
npm run telemetry:toggle
```

---

## Or Use the Script Directly

```bash
# From anywhere
cd /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus

# Turn off
./scripts/telemetry-toggle.sh off

# Turn on
./scripts/telemetry-toggle.sh on

# Check status
./scripts/telemetry-toggle.sh status

# Toggle
./scripts/telemetry-toggle.sh toggle
```

---

## What It Does

**When you turn OFF:**
- Adds `export NUCLEUS_ANON_TELEMETRY=false` to your `~/.zshrc`
- Disables telemetry for current session
- Saves ~10K Upstash commands/day
- Keeps 400K+ headroom for real users

**When you turn ON:**
- Removes the line from `~/.zshrc`
- Enables telemetry for current session
- Your commands get tracked (dogfooding)

---

## Recommended Workflow

**During heavy dev sessions:**
```bash
npm run telemetry:off
```

**When dogfooding/testing real workflows:**
```bash
npm run telemetry:on
nucleus morning-brief  # This will send telemetry
nucleus tasks list
# ... test your workflows ...
npm run telemetry:off  # Turn back off when done
```

**Check status anytime:**
```bash
npm run telemetry:status
# or
/tmp/telemetry_monitor.sh  # Shows full health check + telemetry status
```

---

## Current Usage

- **81K commands** used (16% of 500K free tier)
- **70K** from drain script polling empty queue
- **10K** from your own telemetry
- **0** from external users (yet)

**With telemetry OFF:** You'll save ~10K/day, keeping 430K headroom for real users.

---

## No Changes Made Yet

This is just the tooling. Run `npm run telemetry:status` to see current state, then decide if you want to turn it off.
