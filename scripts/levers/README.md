# Levers — modular operators over the .brain/ substrate

A **Lever** is a small, self-contained unit that reads a manifest, takes
one deterministic local action, and appends one typed observation to
`.brain/ledger/events.jsonl`. Levers never talk to each other; they
compound through the shared substrate.

See [`docs/substrate.md`](../../docs/substrate.md) for the substrate
contract. This README is the **operator author's guide**.

## Anatomy of a lever

```
scripts/levers/
├── base.py              # Lever ABC, LedgerEvent, LeverObservation,
│                        # exceptions, _run_subprocess helper
├── _diff.py             # Shared diff-walker (iter_added_lines)
├── run_lever.py         # Dispatcher: run(name), run_trigger(trigger)
├── manifests/
│   ├── ruff_chain.yaml
│   └── todo_chain.yaml
├── ruff_chain.py        # concrete Lever subclass
└── todo_chain.py
```

## Minimum contract for a new lever

Two files. Same name. Under 60 LOC of Python.

**`scripts/levers/manifests/<name>.yaml`:**

```yaml
name: <name>
description: One sentence — what signal does this lever surface?
enabled: true
triggers:
  - post_executor      # standard: fires after every executor run
  - manual             # standard: `python -m scripts.levers.run_lever <name>`
inputs:
  # lever-specific; lever reads these via manifest["inputs"]
outputs:
  ledger_event_type: lever.<name>.observation
```

**`scripts/levers/<name>.py`:**

```python
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict
from .base import Lever, LeverObservation, SubprocessFailure


class MyLever(Lever):
    name = "my_lever"

    def run(self, manifest: Dict[str, Any], brain_path: Path) -> LeverObservation:
        inputs = manifest.get("inputs", {}) or {}
        # ... do work ...
        try:
            result = self._run_subprocess(
                ["some", "command"], timeout=10, stage="my_stage"
            )
        except FileNotFoundError:
            return self.observation_error("my_stage", "tool not installed")
        if result.returncode == 0:
            return self.observation_clean({"files_checked": 0})
        return self.observation_found({"findings": [...]})
```

## Rules (enforced; do not bypass)

1. **Name must match the manifest stem AND be a Python identifier.**
   The dispatcher validates `name.isidentifier()` before importing.
2. **Subclass `Lever` and set `name` to the manifest stem.** The
   dispatcher finds the right class by name.
3. **Use `self._run_subprocess` for any shell-out.** It validates argv is
   `list[str]`, forbids `shell=True`, and raises `SubprocessFailure`
   (carrying stage/returncode/stderr) on non-zero when `check=True`.
4. **Never `except Exception`.** Catch specific named exceptions —
   `FileNotFoundError`, `subprocess.TimeoutExpired`, `SubprocessFailure`,
   `OSError`, `yaml.YAMLError`, etc. Bare `except Exception` is an
   anti-pattern and will be flagged by the Wave 0 audit linter rule.
5. **Return a `LeverObservation`.** Use the helpers:
   `observation_clean(detail)`, `observation_found(detail)`,
   `observation_error(stage, error, **extra)`,
   `observation_skipped(reason, **extra)`.
6. **Zero hidden state.** Module-local caches are fine; anything another
   lever needs to read goes through the ledger.
7. **No direct writes to `events.jsonl`.** The dispatcher handles append
   under `flock` + `fsync`.

## Outcomes

| Outcome   | When                                                   |
|-----------|--------------------------------------------------------|
| `clean`   | Nothing to report. The ideal case.                     |
| `found`   | Lever detected violations in its scope.                |
| `error`   | Lever failed to execute (tool missing, timeout, etc.). |
| `skipped` | Lever short-circuited (disabled, no inputs, etc.).     |
| `unknown` | Reserved for fail-closed gate reads. Levers don't emit this directly. |

## Triggers

See [`docs/substrate.md#kill-switches`](../../docs/substrate.md) for the
kill-switch keys. Known triggers:

- `post_executor` — after every TB driver executor run
- `pre_commit` — git pre-commit hook
- `post_commit` — git post-commit hook
- `session_start` — Claude Code session boot
- `cron_15m` / `cron_hourly` / `cron_daily` — scheduled
- `manual` — CLI `python -m scripts.levers.run_lever <name>`

## Adding a lever — checklist

```
[ ] Write scripts/levers/manifests/<name>.yaml
[ ] Write scripts/levers/<name>.py — subclass Lever, set name, implement run
[ ] Add tests to tests/test_levers.py under a new class TestNameLever
[ ] Confirm: python -m scripts.levers.run_lever <name>  → expected outcome
[ ] Confirm: pytest tests/test_levers.py -q             → green
[ ] Confirm: python bin/lever_wave0_audit.py            → all 5 criteria pass
```

## Why the constraints are strict

Every constraint prevents a class of bug that would fan out across 29
levers. Bare `except Exception` in one lever is a nuisance; in 29 it's a
silent-failure plague. The contract ships the guardrails once so every
lever inherits them.

See [`docs/lever_runbook.md`](../../docs/lever_runbook.md) for incident
response when a lever misbehaves in production.
