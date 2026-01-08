---
description: Run Nucleus health check and analytics
---

# Nucleus Health Check Workflow

This workflow generates comprehensive analytics about the Nucleus ecosystem.

## Quick Check

// turbo
```bash
cd /Users/lokeshgarg/ai-mvp-backend
export NUCLEAR_BRAIN_PATH=/Users/lokeshgarg/ai-mvp-backend/.brain
python3 scripts/nucleus_health_check.py
```

## With Event Emission

```bash
cd /Users/lokeshgarg/ai-mvp-backend
export NUCLEAR_BRAIN_PATH=/Users/lokeshgarg/ai-mvp-backend/.brain
python3 scripts/nucleus_health_check.py --emit-event
```

## What It Shows

1. **Satellite View** - Current depth, activity, sprint status
2. **Metrics** - Velocity, closure rates, mental load
3. **Health** - Open loops, tier breakdown, advice
4. **Tasks** - Pending items
5. **Events** - Recent event stream activity

## Reports Saved To

- `.brain/meta/health_checks/health_check_YYYYMMDD_HHMMSS.txt` - Human readable
- `.brain/meta/health_checks/health_check_YYYYMMDD_HHMMSS.json` - Machine readable

## Schedule (Optional)

Add to crontab for daily health checks:

```bash
# Every morning at 9am
0 9 * * * cd /Users/lokeshgarg/ai-mvp-backend && python3 scripts/nucleus_health_check.py --emit-event >> /tmp/nucleus_health.log 2>&1
```

## Related Commands

View recent health checks:
```bash
ls -lht .brain/meta/health_checks/ | head -10
```

View latest report:
```bash
cat .brain/meta/health_checks/health_check_*.txt | tail -100
```

## Integration with Analytics Dashboard

After running health check, view the analytics dashboard:
```bash
cat .gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NUCLEUS_ANALYTICS_DASHBOARD.md
```
