# Fix Cron Environment Variables

> **Issue:** Cron doesn't inherit shell environment variables  
> **Solution:** Export API keys to cron's environment

---

## Quick Fix (Option 1: Edit Crontab Directly)

Run this command:
```bash
crontab -e
```

Add these lines at the TOP of your crontab (before the cron jobs):
```bash
GEMINI_API_KEY=<your_key_from_.env>
TELEGRAM_BOT_TOKEN=<your_token_from_.env>
```

Then save and exit.

---

## Better Fix (Option 2: Load from .env)

Update your cron entries to source .env first:

```bash
0 8 * * * cd /Users/lokeshgarg/ai-mvp-backend && source .env && /usr/bin/python3 /Users/lokeshgarg/ai-mvp-backend/scripts/nightly_agent.py >> /Users/lokeshgarg/ai-mvp-backend/.brain/ledger/cron.log 2>&1

0 9 * * 0 cd /Users/lokeshgarg/ai-mvp-backend && source .env && /usr/bin/python3 /Users/lokeshgarg/ai-mvp-backend/scripts/weekly_summary.py >> /Users/lokeshgarg/ai-mvp-backend/.brain/ledger/cron.log 2>&1
```

---

## Verify It Works

After fixing, test the nightly agent manually:
```bash
cd /Users/lokeshgarg/ai-mvp-backend
source .env
python3 scripts/nightly_agent.py
```

If that works, cron will work too.

---

**Do you want me to walk you through Option 1 or Option 2?**
