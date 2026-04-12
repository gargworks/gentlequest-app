# TODOS — Lever Substrate

Deferred work surfaced during plan-eng-review of the Wave 6 scope
(bull_audit meta-lever + chat event publisher retrofit). Each entry
has enough context that a 3-months-later pickup can proceed without
re-deriving the motivation.

---

## 1. Ledger rotation — `events.YYYY-MM.jsonl` + `events.current.jsonl` pointer

**What:** Partition `.brain/ledger/events.jsonl` by month. Writers
target `events.current.jsonl` (a pointer file / symlink). Readers can
tail a window or enumerate rotated files for historical queries.

**Why:** The ledger is append-only with no rotation. As of
Wave 5 it's already 3000+ lines and growing. Every process that reads
the full file (TB driver gate scan, bull_audit without windowing,
`jq` queries) pays O(N) that grows forever. `bull_audit`'s
`window_events=1000` is a workaround, not a fix.

**Pros:** Bounded read cost, natural archival unit, predictable
disk footprint.

**Cons:** Every ledger writer must respect the pointer; rollover
logic needs atomic swap; every existing reader needs a "follow the
pointer" update. Non-trivial migration — touches `append_observation`,
TB driver gate, wave0 audit, and every `jq .brain/ledger/events.jsonl`
invocation in scripts.

**Depends on / blocked by:** None. Self-contained substrate change.

**Current state:** Pointer file pattern exists in design (foundation
commit `39909ee6` deferred this). Empty `.brain/ledger/event_schema.json`
also sits unused — reconciliation is part of this work.

**Where to start:** `scripts/levers/run_lever.py::append_observation`.
Add rotation check before flock acquire: if current month != file month,
swap pointer.

---

## 2. Brazen Bull invariant library — beyond the 5-check skeleton

**What:** Expand `bull_audit`'s invariant list as failure modes
are discovered. Candidate next invariants:
- `manifest_not_drifting` — no YAML key outside the frozen schema
- `lever_count_monotone` — number of enabled levers per trigger never
  drops without a corresponding removal commit
- `trigger_dispatch_healthy` — every trigger fires levers within
  N minutes of its cron, no hung dispatches
- `test_matrix_coverage` — every lever has ≥5 tests (CI assertion
  lifted into runtime)
- `ledger_monotone_ts` — timestamps are weakly increasing (detects
  clock skew or file rewrite)

**Why:** The 5-invariant skeleton (`schema_valid`, `outcome_in_set`,
`duration_bounded`, `csr_not_collapsed`, `no_repeated_lever_errors`)
covers *runtime integrity*. It does not cover *structural drift*
(manifests being edited by hand, lever files being deleted,
CI coverage regressions). Those are the kinds of bugs that compound
silently — exactly what Brazen Bull exists to catch.

**Pros:** Each new invariant shrinks the "silent rot" surface. Cheap
per-invariant implementation (~15 LOC each) once the framework lands.

**Cons:** Discovery is ongoing — premature lock-in to the full list
risks false positives and rule-lawyering. Add-one-at-a-time when
evidence of a specific failure mode arrives.

**Depends on / blocked by:** Wave 6 bull_audit shipping with the
5-check skeleton. Expansion is additive.

**Where to start:** `scripts/levers/bull_audit.py` — add invariant
functions alongside the initial 5. Each invariant is a pure function
`(events: list, csr: float, manifests_dir: Path) -> Optional[str]`
returning a finding string or None.

---

## 3. Chat event publisher — backpressure / flock contention under load

**What:** Investigate whether `append_observation`'s `fcntl.flock`
becomes a request-latency bottleneck once chat QPS climbs past ~1
sustained. If it does, implement a bounded async queue (daemon thread
pulls events off an `asyncio.Queue` / `queue.Queue` and flushes them
to the ledger in batches).

**Why:** The lever substrate's `append_observation` holds an
exclusive file lock for the duration of a write + fsync. For cron
levers (firing seconds or minutes apart) that's fine. For chat events
firing on every request, lock contention is a real risk at scale.
Critical failure mode flagged in Wave 6 plan-eng-review: silent latency
degradation — the request still succeeds, it just slowed down by the
flock wait.

**Pros:** Keeps the synchronous contract for levers while letting
request-path event emission be non-blocking. No change to lever
contract.

**Cons:** Ordering guarantees weaken (events may flush out-of-arrival-
order if batched). Requires a durable queue (lose-on-crash acceptable
for chat events but must be explicit). Daemon thread = lifecycle
bug surface.

**Depends on / blocked by:** Wave 6 chat publisher shipping (so we
have events to benchmark). Benchmark with a load-gen harness before
deciding between "live with it," "non-blocking queue," or "per-writer
ledger partition."

**Current state:** Zero chat users today. The chat publisher ships
in Wave 6 with synchronous `append_observation`. This TODO is the
follow-up once usage data says lock contention matters.

**Where to start:** Benchmark first — `tests/benchmarks/chat_event_qps.py`
or similar. If p99 request latency degrades >10ms vs. no-emit baseline
at target QPS, build the queue.

---

## Unresolved decisions from Wave 6 plan-eng-review

None. All 4 review issues and all 3 TODOs had a clear user response.
