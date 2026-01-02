# 📚 Documentation Index

> Last updated: 2026-01-02

## Core Documentation

| Document | Purpose |
|----------|---------|
| [README.md](../README.md) | Project overview |
| [API_DOCUMENTATION.md](../API_DOCUMENTATION.md) | API endpoints |
| [DEPLOYMENT.md](../DEPLOYMENT.md) | Deployment guide |
| [TESTING_GUIDE.md](../TESTING_GUIDE.md) | Testing procedures |

## Operational

| Document | Purpose |
|----------|---------|
| [AGENTS.md](../AGENTS.md) | Agent roster and roles |
| [RELEASES.md](../RELEASES.md) | Release history |
| [DEPLOYMENT_PROTOCOL.md](../DEPLOYMENT_PROTOCOL.md) | Deploy procedures |
| [PRODUCTION_DEPLOYMENT_GUIDE.md](../PRODUCTION_DEPLOYMENT_GUIDE.md) | Production deploy |

## Development

| Document | Purpose |
|----------|---------|
| [DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md) | Coding standards |
| [LOCAL_TESTING_CHECKLIST.md](../LOCAL_TESTING_CHECKLIST.md) | Local test steps |
| [FEATURE_PLANNING_TEMPLATE.md](../FEATURE_PLANNING_TEMPLATE.md) | Feature template |

## Architecture

| Document | Purpose |
|----------|---------|
| [SYSTEM_INTEGRATION.md](../SYSTEM_INTEGRATION.md) | System overview |
| [SINGLE_CODEBASE_GUIDE.md](../SINGLE_CODEBASE_GUIDE.md) | Codebase structure |
| [SHARED_HISTORY_PROTOCOL.md](../SHARED_HISTORY_PROTOCOL.md) | Agent memory |

## Brain / Nucleus

| Document | Purpose |
|----------|---------|
| [nucleus/README.md](../nucleus/README.md) | Nucleus brain package |
| [.brain/context.md](../.brain/context.md) | Brain context |
| [.brain/patterns.md](../.brain/patterns.md) | Agent patterns |

## Archive

Stale documentation moved to [`docs/archive/`](./archive/).
See [ARCHIVE.md](./ARCHIVE.md) for archive log.

---

## Quick Links

- **Run health check:** `python3 scripts/flight_check.py`
- **Check brain status:** `PYTHONPATH=. python3 nucleus/clients/cli/nucleus_cli.py status`
- **Master controller:** `python3 scripts/ops/master_controller.py status`
