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

## 4. gt40_typecheck + gt40_test_smoke — `--json` receipt — **DONE**

Both levers rewritten to use `nucleus verify --tiers <chain> --json`
and parse the structured receipt. Shared helper at
`scripts/levers/_gt40.py` (`parse_receipt`, `classify_receipt`,
`build_argv`).

Live-fire confirms outcome routing works: both fire `clean` against
the real env (tiers reached as expected); pre-rewrite ledger entries
showed `found` with INSECURE-MODE / GROUND-FAIL noise.

**Surprise discovery:** `nucleus verify` never accepted `--smoke` —
argparse rejected it with exit 2, generating the bulk of the noise
(usage-text-as-findings). Removed the input + bogus flag entirely.

`gt40_lint` (tier 1) NOT migrated — it works cleanly on the old
contract and the helper is now available if a future need surfaces.

---

## 5. license_header_check — re-enable when repo adopts a header convention

**What:** Flip `scripts/levers/manifests/license_header_check.yaml`
`enabled: false` → `true` once the project commits to a license-header
convention (SPDX identifier, copyright notice, or similar).

**Why:** Nucleus has no established convention — zero existing source
files carry any kind of license/copyright header. With the lever
enabled, every new file is flagged, generating pure noise. Disabled
until the repo decides it wants headers.

**Pros:** Cheap to re-enable (one YAML flag). Lever + tests retained.

**Cons:** None while disabled — if the decision is "no headers," the
lever can be deleted entirely. Keeping it is a bet on eventual adoption.

**Depends on / blocked by:** Explicit decision on whether Nucleus code
carries headers (likely tied to open-source distribution strategy).

**Current state:** Lever disabled, rationale in manifest. Live-fire
evidence: 20 findings in ledger tail-500 before disabling, all against
legitimately new files with no actual policy violation.

**Where to start:** Decide convention. Example header for Python:
`# SPDX-License-Identifier: <id>` on line 1. Then flip manifest flag.

---

## Unresolved decisions from Wave 6 plan-eng-review

None. All 4 review issues and all 3 TODOs had a clear user response.

---

## TODO 6 — `.brain/audit/results.json` atomic write — **DONE**

Shipped during Wave 7 live-fire follow-up. `_record_audit_result` now
writes to `.json.tmp` then `os.replace` swaps atomically.

Test: `tests/test_lever_compounding.py::TestRecordAuditResultAtomic::
test_concurrent_readers_never_see_partial_write` hammers 4 reader
threads against 10 sequential writes — zero `JSONDecodeError`.

The lever's `_load_results_with_retry` retry-once is now defensive
overkill at the source but kept for safety against any future writer
that bypasses `_record_audit_result`.

---

## TODO 7 — shared ledger-tail reader helper — **DEFERRED (re-evaluated 2026-04-13)**

**Original premise:** three callers copy "open, tail N, parse" — extract
to `_ledger_reader.read_window`.

**Re-evaluation finding:** the three callers have meaningfully *different*
semantics — extracting forces conformity that isn't actually shared.

| Caller | Parse strategy | Walk | Error policy |
|---|---|---|---|
| `bull_audit._read_window` | `LedgerEvent.from_jsonl` strict + grandfather legacy count | forward, last N | OSError → `(empty, 0)` |
| `_lever_gate_scan` | raw `json.loads`, filter `lever.*.observation found` | forward, last N | OSError → status=`unknown` (fail-closed gate) |
| `_spawn_plan_audit_fix_tasks` | raw `json.loads`, single newest match | reverse, all lines | OSError → emit `skipped` ledger event, return `[]` |

The genuinely shared code is just `path.read_text(encoding="utf-8")
.splitlines()` + OSError handling. A helper that exposes only that is
too thin to be worth the import. A helper that exposes parsing/walking
bakes in policy choices that would force migrations to **change**
behavior (e.g., `_lever_gate_scan` inheriting bull_audit's grandfather
counting it doesn't want).

**Re-trigger criteria (when to revisit):**

1. A 4th caller appears AND its parse/walk semantics overlap with one
   of the existing three. Three is coincidence; four with the same
   shape is a pattern.
2. Ledger rotation (TODO 1) lands. Once readers must enumerate
   `events.YYYY-MM.jsonl` segments + follow `events.current.jsonl`
   pointer, the seek-by-time logic IS genuinely shared and worth
   centralizing — but it'd be a `tail_events_since(ts)` helper, not
   the originally-proposed `read_window(path, n)`.
3. A real lock-acquire policy gets defined (today there is none on the
   read path; writers use flock, readers don't). If shared lock
   semantics emerge, that's a true shared concern.

Until any of those hit, the duplication is honest — three small reads
with three different error stories — and consolidating now would be
premature abstraction.

---

## 8. Classifier dispatch-table refactor — trigger at bucket #11

**What:** Refactor `scripts/levers/plan_audit.py::_classify` from if-elif
cascade into an ordered list `[(predicate_fn, bucket_name), ...]`
iterated in priority order (first match wins).

**Why:** Wave 9 lands the classifier at 10 classifying buckets +
`parse_error` (reached only via the run-level except). Adding an 11th
classifying bucket (e.g. `reject_recurring`, `plan_family_drift`) would
push the `_classify` cyclomatic complexity past the 10-branch threshold
flagged in Wave 8/9 plan-ceo-review.

**Pros:** Data-driven priority makes ordering testable in isolation;
moving a bucket's priority becomes a list reorder rather than a diff
across the if-elif chain. Keeps each predicate independently unit-
testable.

**Cons:** Premature until bucket #11 exists. Adds an indirection
layer and slightly obscures the current linear reading order. Would
also need a way to express the unverifiable → never_audited short
circuit that currently lives in the early-return.

**Re-trigger criteria:** Adding an 11th classifying bucket to
`_classify`. At that point the refactor is ~30 LOC: extract predicates
into module-level callables, flatten the cascade, and keep the
per-plan try/except (R3) wrapping the iteration.

**Where to start:** `scripts/levers/plan_audit.py::_classify` —
extract into a module-level
`_CLASSIFIER_CHAIN: list[tuple[Callable, str]]`; `_classify` becomes
a 3-line loop returning the first matched bucket. Add a per-chain
ordering test alongside the existing bucket tests.
