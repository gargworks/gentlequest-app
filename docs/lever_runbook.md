# Lever Substrate — Incident Runbook

When a lever misbehaves in production. Focused on the five scenarios the
substrate posture is designed to catch.

## 1. Noisy lever (spams DEEPEN on every review)

**Signal:** review_log.jsonl shows `lever_gate_fired: true` on most
recent reviews; `lever_gate_count` high; same `lever_gate_types`
repeating.

**Triage:**

```bash
jq -r 'select(.lever_gate_fired) | .lever_gate_types[]' \
    .brain/driver/review_log.jsonl | sort | uniq -c | sort -rn
```

**Containment (in order of reversibility):**

1. Disable the lever via its manifest: set `enabled: false` in
   `scripts/levers/manifests/<name>.yaml`. Commit. Cheapest.
2. If multiple levers are noisy: flip `lever_gate_enabled: false` in
   `.brain/driver/config.json`. Gate short-circuits to ACCEPT. Levers
   still fire and record observations.
3. Nuclear: flip `lever_substrate_enabled: false`. Dispatcher is a no-op.
   Only use when a lever is actively corrupting the substrate.

**Post-incident:** re-run the lever's tests; add a regression test for
the false-positive pattern; re-enable.

## 2. False ACCEPT (review rubber-stamps despite real findings)

**Signal:** manually-inspected review has clear violations but
`verdict: ACCEPT` and `lever_gate_fired: false`.

**Triage:**

```bash
# What did the ledger say about this file right before the review?
jq 'select(.type | startswith("lever.") and endswith(".observation"))' \
    .brain/ledger/events.jsonl | tail -100
```

Check:

- Was the relevant lever enabled in its manifest?
- Did `run_trigger('post_executor')` fire for the executor run?
- Does the finding text include the diff file path? Gate matches on
  substring overlap between findings and diff files — findings that
  don't reference the file path won't match.

**Fix:** if the lever isn't naming the path in its findings, that's a
lever bug (add the path prefix). If the gate scan is returning empty
when the ledger has matches, check for corruption via Wave 0 audit
criterion 2.

## 3. Dispatcher hang (pre-commit / post-executor doesn't return)

**Signal:** TB driver sits on `run_trigger('post_executor')`; no new
ledger events for 30+ seconds.

**Triage:** find the stuck subprocess:

```bash
ps -ef | grep -E "(ruff|git|python -m scripts.levers)"
```

**Containment:**

1. Kill the stuck subprocess. The lever should fail with `TimeoutExpired`
   and emit a `lever.dispatcher.failure` event.
2. If TB is still hung, the lever may have forked a detached child — kill
   by process tree.
3. Flip `lever_substrate_enabled: false` to stop future firings.

**Fix:** the lever MUST pass a `timeout` to `_run_subprocess` — that's
the contract. Grep for the lever name and verify it's using
`self._run_subprocess(..., timeout=N, ...)` not raw `subprocess.run(...)`.

## 4. Ledger corruption (JSON parse errors on tail)

**Signal:** `lever.schema.violation` events in the ledger; or readers
(the TB gate) logging "ledger unreadable — forcing DEEPEN".

**Triage:**

```bash
# Count invalid lines
python3 -c "
from pathlib import Path
from scripts.levers.base import iter_events, LedgerSchemaError
path = Path('.brain/ledger/events.jsonl')
good = bad = 0
with path.open() as f:
    for line in f:
        if not line.strip():
            continue
        try:
            from scripts.levers.base import LedgerEvent
            LedgerEvent.from_jsonl(line)
            good += 1
        except LedgerSchemaError:
            bad += 1
print(f'good={good} bad={bad}')
"
```

**Fix:**

1. If 0–few bad lines: leave them. `iter_events(skip_invalid=True)`
   tolerates them. The gate's `unknown` sentinel is the safety net.
2. If many bad lines: the concurrent-write lock may have been bypassed.
   Check for non-dispatcher writers to `events.jsonl` via:
   `grep -rn "events.jsonl" scripts/ backend/`.
3. Archive the current ledger (`mv events.jsonl events.corrupt-YYYYMMDD.jsonl`)
   and start fresh. Lose historical observations — acceptable; they're
   recomputable.

## 5. TB gate forces DEEPEN forever (fail-closed sentinel stuck)

**Signal:** every review comes back DEEPEN; `lever_gate_status: unknown`
in every review_log entry.

**Triage:** the gate is reporting unknown because it can't read the
ledger.

```bash
ls -la .brain/ledger/events.jsonl .brain/ledger.lock
```

**Fix:**

- Permissions wrong? `chmod 0644 .brain/ledger/events.jsonl`
- Ledger is a directory? Remove it, create empty file.
- Lock file stuck open? Kill any dispatcher processes; the lock file
  itself is safe to `rm` when no process holds it.

## Kill switch reference

```bash
# Disable one lever (preferred, reversible):
# edit scripts/levers/manifests/<name>.yaml → enabled: false

# Disable the gate (ACCEPT is always honored):
# edit .brain/driver/config.json → "lever_gate_enabled": false

# Disable the entire substrate (dispatcher is a no-op):
# edit .brain/driver/config.json → "lever_substrate_enabled": false
```

All three default to safe-on. Flip to disable. Flip back when fixed.

## Wave 0 audit as diagnostic

Run the Wave 0 audit as a smoke test at any time:

```bash
python3 bin/lever_wave0_audit.py --verbose
```

5 criteria:

1. Ledger grows by enabled-lever-count
2. Each new line validates against `LedgerEvent`
3. Dispatcher executes without raising
4. TB driver gate helpers import + are callable
5. Fail-closed sentinel works on unreadable ledger

If any fail, the contract is broken — do not ship until all five pass.
