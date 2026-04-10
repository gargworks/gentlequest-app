# CSR — Claim Survival Rate (Public Spec v0.1)

> A measurement protocol for AI agent trustworthiness over time.

## Why this spec exists

Every AI agent makes claims: "the test passes," "the migration is safe," "the
PR is ready to merge." Over the lifetime of an agent, the only thing that
matters is what fraction of those claims **survive independent verification**.
Not what the agent intended. Not what the agent reported. What was true after
something else looked.

CSR is the scalar that summarizes this. It is intentionally simple, because the
moment a trust metric becomes complicated it becomes negotiable.

## Definitions

- **Claim.** An assertion the agent makes that something is true. Examples:
  a unit test passing, a CI run going green, a verification tier (Tier 0–5)
  reporting success, a driver phase completing, a PR being merged.
- **Survival.** A claim survives when an independent process — one the agent
  did not choose for itself — confirms the claim under conditions the agent
  did not control. Examples: the same test passing on a clean machine, a
  reviewer accepting the PR, a downstream task using the artifact without
  hitting the failure mode.
- **CSR.** `survived / total`, computed continuously. A scalar in `[0.0, 1.0]`.

## Founding claim

CSR starts at `1.0`. The first claim is the activation commit itself —
proven by the hermetic test suite that ships alongside the implementation. This
is a **founding claim**, not a runtime claim. The whole point of the rest of
the system is to keep CSR close to 1 as runtime claims accumulate and the mix
shifts away from the founding claim.

CSR starting at 0 is a category error. There is no way to "honestly" start at
0 — there is no claim to be 0/0 over. The activation event is the first claim.

## Measurement rules

1. Every claim is recorded with: `at`, `step`, `phase` (optional),
   `survived: bool`, `reason` (if not survived). No other fields are required;
   none are forbidden.
2. Every survived claim increments both `claims_total` and `claims_survived`.
3. Every unsurvived claim increments only `claims_total`.
4. `ratio = claims_survived / max(claims_total, 1)` — always rounded to 4
   decimal places when serialized.
5. `recent_claims` is a bounded ring buffer (≤ 50 entries) holding the most
   recent claims for at-a-glance review.

## Reference implementation

The reference implementation lives at
`mcp-server-nucleus/src/mcp_server_nucleus/flywheel/csr.py`. The headline
functions are `read_csr`, `bump_survived`, and `bump_unsurvived`.

```python
from mcp_server_nucleus.flywheel import bump_survived, bump_unsurvived, read_csr

bump_survived(brain_path, step="phase_a:task_001")
bump_unsurvived(brain_path, step="phase_d:task_002", reason="reviewer crashed")

state = read_csr(brain_path)
# {"claims_total": 3, "claims_survived": 2, "ratio": 0.6667, ...}
```

## On-disk format

`csr.json` lives at `<brain>/flywheel/csr.json` and is written atomically. The
file is a disposable cache: a corrupted file resets to the founding state
rather than crashing the caller. CSR is not a sacred ledger.

```json
{
  "claims_total": 3,
  "claims_survived": 2,
  "claims_unsurvived": 1,
  "ratio": 0.6667,
  "first_claim_at": "2026-04-10T00:00:00+00:00",
  "last_updated": "2026-04-10T00:01:23+00:00",
  "recent_claims": [
    {"at": "...", "step": "phase_a:task_001", "survived": true},
    {"at": "...", "step": "phase_d:task_002", "survived": false, "reason": "reviewer crashed"}
  ]
}
```

## Reporting CSR

When citing CSR, always disclose three things:

1. **Window.** "Lifetime CSR" (since first_claim_at) or "rolling-N CSR" (last
   N claims). Don't mix the two.
2. **Source.** Which brain instance produced the claims. CSR is not a global
   number — it is per-system.
3. **Mix.** Whether the denominator is dominated by founding claims or
   runtime claims. A 1.0 CSR with 5 claims is barely meaningful; 1.0 with
   500 claims is.

## Badge format (proposed, deferred)

`![CSR](https://flywheel.nucleus.dev/badge/owner/repo.svg)` — endpoint deferred
to v1.0. The badge will read the latest `csr.json` from the linked brain and
render `survived/total — ratio%`.

## Anti-patterns

- **Counting your own grader.** If the agent decides whether the claim
  survived, the survival is not independent. Every CSR bump must be triggered
  by an entity downstream of the claim — CI, a reviewer, a verification tier,
  a downstream task.
- **Resetting to manage perception.** A drop in CSR is signal. Resetting after
  a bad week erases the signal and trains future-you to distrust the metric.
- **Aggregating across systems.** Two brains do not have a meaningful average
  CSR. Report them separately.
- **Hand-editing `csr.json`.** It is silently clobbered on the next write. If
  you need to backfill, append to `recent_claims` via the API, not the file.

## Changelog

- **v0.1** (2026-04-10): initial public draft. Frozen for the Mount Everest
  launch. v1.0 will follow once we have ≥ 50 systems reporting CSR over ≥ 90
  days of mixed runtime claims.
