# The Nucleus Substrate — Contract

> **One named substrate + N modular operators.**
> Operators declare what they read from / write to the substrate via typed
> events. They never talk to each other directly. Orchestrators consume
> events, never internals. Compounding comes from the substrate;
> modularity comes from the operators; together they are superlinear.

Three platforms ran the modular+compounding curve for a decade+ and reached
planetary scale: Unix (pipes + filesystem), Git (object DAG), Kubernetes
(etcd). All three share the same shape — small modules, one named shared
substrate. Nucleus's substrate is **`.brain/`**, centered on
`.brain/ledger/events.jsonl` as the single ordered event stream.

## 1. The event stream

**Path:** `.brain/ledger/events.jsonl`

**Shape:** append-only JSONL. One event per line. Never rewritten. Never
truncated (rotation deferred; see [Deferred](#deferred) below).

**Reads:** every consumer tails or slices the file by type. MCP
`brain://ledger/events` surfaces cross-session reads.

**Writes:** every module appends via a validated helper —
[`scripts.levers.run_lever.append_observation`](../scripts/levers/run_lever.py)
for levers; module-local helpers for legacy monoliths. Direct file writes
are discouraged — concurrent writers WILL corrupt JSONL without the
advisory lock.

**Advisory lock:** `.brain/ledger.lock`. `append_observation` acquires
`flock(LOCK_EX)` for the duration of the write + `fsync`, releases on
error or success. Non-lever writers that bypass the lock risk interleaved
lines.

## 2. Event type convention

New types follow `<module>.<action>.<phase>`:

| Type | Producer | Body |
|------|----------|------|
| `lever.<name>.observation` | Lever dispatcher | `{lever, outcome, detail, duration_ms}` |
| `lever.schema.violation` | `append_observation` | `{lever, error, observation_outcome}` |
| `lever.dispatcher.failure` | `run_trigger` | `{lever, trigger, error, error_class}` |
| `lever.manifest.error` | `run_trigger` | `{lever, trigger, error}` |
| `tb.review.decided` | TB driver | `{task_id, verdict, original_verdict, confidence, lever_gate_fired, lever_gate_status}` |

**Grandfathered one-token types** (existing producers keep working):
`session_saved`, `engram_written`, `health_status`, `task_created`,
`ground_verified`, `LLM_GENERATE`, `slot_registered`,
`depth_increased`, `depth_decreased`, `session_registered`,
`task_claimed`, `task_state_changed`, `code_critiqued`. New types MUST
use the dotted form.

## 3. Required fields

Every event MUST carry:

- `ts` — ISO-8601 datetime string (UTC preferred)
- `type` — dotted string or grandfathered token

Lever observations additionally carry:

- `lever` — string, matches the manifest stem
- `outcome` — one of `clean | found | error | skipped | unknown`
- `detail` — object (lever-specific payload)
- `duration_ms` — non-negative int (dispatcher-injected)

Schema validation lives in
[`scripts/levers/base.py::LedgerEvent`](../scripts/levers/base.py). Use
`LedgerEvent.from_jsonl(line)` when reading; it raises
`LedgerSchemaError` on malformed input. Use `LedgerEvent.to_jsonl()` when
writing; the dispatcher does this automatically for levers.

## 4. Write contract

```python
from scripts.levers.run_lever import append_observation

append_observation(
    lever_name="ruff_chain",
    observation={"outcome": "clean", "detail": {"files_checked": 0}},
)
```

Rules:

- `outcome` MUST be in `{clean, found, error, skipped, unknown}`.
- `detail` MUST be a dict. Control characters are stripped server-side.
- Writes acquire the advisory lock, write, flush, `fsync`, release.
- Schema violations emit `lever.schema.violation` AND raise
  `LedgerSchemaError`.

## 5. Read contract

```python
from scripts.levers.base import iter_events
from pathlib import Path

for event in iter_events(Path(".brain/ledger/events.jsonl")):
    if event.type.startswith("lever.") and event.outcome == "found":
        ...
```

`iter_events(skip_invalid=True)` silently skips corrupt lines (default).
Pass `skip_invalid=False` to raise on corruption — readers that need
tamper-evidence (Brazen Bull) should use strict mode.

## 6. No private inter-module state

If two modules need to share a piece of state, it is an event type —
not a file, not a database row, not a shared variable. Module-local
caches are fine (write-through to the ledger is the canonical path).

## 7. Failure posture — FAIL CLOSED on reads

Every reader that gates ACCEPT/DEEPEN decisions MUST treat read failures
as `unknown`, not `clean`. The TB driver's `_lever_gate_scan` is the
reference implementation: when the ledger is unreadable, it returns
`status=unknown`, which forces DEEPEN.

**Why:** a silent ACCEPT on unknown ledger state is the worst failure
mode of the whole substrate. Better to DEEPEN unnecessarily than to
ACCEPT in the dark.

## 8. Kill switches

Top-level keys in `.brain/driver/config.json`:

- `lever_substrate_enabled` — when false, dispatcher is a no-op and the
  TB gate is disabled. Default true.
- `lever_gate_enabled` — when false, TB review gate never downgrades
  ACCEPT. Default true.

Both default to true. Flip to disable if a lever causes runtime damage;
fix and flip back.

## Deferred

- **Ledger rotation** — `events.YYYY-MM.jsonl` + `events.current.jsonl`
  pointer. Not needed until firehose compiles materially.
- **Cross-brain federation** — multi-device substrate is Phase N+1.
- **Recipes layer** — sequence-of-levers with typed I/O. Add when 3+
  workflows need the same lever composition.
- **Schema registry** — `.brain/ledger/event_schema.json` currently holds
  a separate legacy agent-routing schema; ledger schema is defined in
  code (`LedgerEvent`) for now.
