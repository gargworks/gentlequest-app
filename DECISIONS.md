# Decisions Log (Append-Only)

> ADR format: Nygard-style, one paragraph per decision. Append only — never rewrite history. Amendments are new ADRs that supersede earlier ones explicitly. Dated; cited in commit messages as `ADR-NNN`.

---

## ADR-001 (2026-05-10): Track A first, Track B parallel signal-only

**Decision:** Build Track A (developer daemon) full-effort in the 90-day window. Run Track B (consumer scout) in parallel as signal-only — landing page, waitlist, user interviews, paid-post canary — with **zero product code** until the Day-30 gate. Reject Track C (BFSI / Axis-internal) for the entire 90-day window; Track C stays parked until its own bright-line fires (Track A or B revenue + organic enterprise design-partner LOI).

**Reason:** Substrate fit is 100% on Track A and ~30% on Track B. Track A time-to-revenue is 4-6 weeks; Track B is 12-16 weeks and faces ChatGPT-Memory as a free, bundled, default-on incumbent. Track C has a 9-12 month enterprise sales cycle incompatible with the bright-lines and is architecturally wrong for bank-managed devices (DLP / pip-blocked / proxy-restricted) — see `PLAN.md ## Track C`.

---

## ADR-002 (2026-05-10): Go for daemon hot path, not Bun/TypeScript

**Decision:** Hot-path daemon written in **Go**. Python becomes a slow-path sidecar (skill execution, swarm orchestration). Tauri (Rust + WebView) for desktop UI in W2-3.

**Reason:** P95 <100ms target requires <50MB RAM resident and zero cold-start cost. The OSS-failure pattern (slow Python daemons) reproduces if we ship Python in W1; users forgive feature-light, they do not forgive slow. Go ships fastest at adequate perf with Lokesh-as-reviewer; Rust is best long-term but too risky for W1. **Fallback documented:** Bun + TypeScript if Go ergonomics block W1 (Lokesh has more JS background; this is a course-correction path, not a pivot).

---

## ADR-003 (2026-05-10): Pseudonymous identity until Day-30 felt-win marker

**Decision:** Eidetic Works runs pseudonymous. Lokesh's name is not attached publicly until either (a) the Day-30 felt-win marker fires (5+ paid Pro), at which point the Anthropic Pioneer disclosure note goes out (see ADR-007), or (b) the Day-60 kill-fire forces a career-capital pivot in which case pseudonymity is dropped on Lokesh's terms.

**Reason:** Axis Bank moonlight-policy risk is binding. VP role + ~₹70L compensation is the floor; product income has to clear an independent self-funding bar before identity exposure. WHOIS privacy + separate GitHub identity + scrubbed commit emails all support this; pseudonymity is fragile (whois / commit-email forensics / resume cross-reference can break it) and the plan accepts this risk as graceful-failure mode.

---

## ADR-004 (2026-05-10): $29 Pro tier, $99 Pro+ tier, $299 Team tier

**Decision:** Pricing ladder: Free (daemon binary, memory-only) / Pro $29-mo (compliance + swarms + dashboard) / Pro+ $99-mo (TB Personal AI sovereign model) / Team $299-mo (multi-seat, shared memory, audit log).

**Reason:** Unit-economics worksheet (`unit-economics.md`) shows ~70% gross margin at $29 with current cost estimates ($0.50-3/mo Anthropic API + $0.10-0.50/mo Cloudflare D1 + $0.08/mo R2 + Stripe 2.9%). Pro+ adds the differentiated wedge (sovereign model). Team is the upgrade path. Pricing is **provisional** — first 3 paid-customer debrief calls (W4-W5) inform any adjustment, logged as ADR-NNN at that time.

---

## ADR-005 (2026-05-10): Cloudflare D1 + R2 + Workers for cloud-sync (not Supabase, not AWS)

**Decision:** Cloud sync runs on Cloudflare Workers + D1 (SQLite-at-edge) + R2 (encrypted backup). Auth via Clerk. Billing via Stripe. Not Supabase. Not AWS.

**Reason:** Per-user marginal cost ceiling is the binding constraint at low scale (free tier covers ~10K MAU at <$50/mo total). Edge latency from D1 is sub-50ms P50 globally. Single-vendor for compliance simplicity. Substrate is portable (Go + standard libs) so Fly.io / Hetzner is a 1-2 day pivot if Cloudflare's free tier terms change. **Pre-portfolioing across providers is YAGNI until traffic warrants.**

---

## ADR-006 (2026-05-10): Day-60 hard kill at <5 paid Pro

**Decision:** If Track A has <5 paid Pro on **2026-07-08** (Day 60), the product business is killed regardless of Track B status. Substrate becomes a portfolio piece + research artifact. Career-capital pivot begins Day 61.

**Reason:** 3 paid would be noise (could be friend-buys); 5 is signal that the message converts. The bright-line is **operator-set with override-restricted authority** — moving the threshold requires a `PLAN.md` amendment ADR with cc-peer sign-off. The function-encoded gate logic in `PLAN.md ## Determinism + autopilot` refuses to recompute against shifted thresholds without the ADR. Bias on ambiguity = kill, not continue.

---

## ADR-007 (2026-05-10): Anthropic Pioneer disclosure at Day-30 felt-win marker

**Decision:** When the first 5 paid Pro signups land (Day-30 felt-win marker), Lokesh sends a short personal note to the Anthropic Pioneer program manager disclosing Eidetic Works. Pre-drafted message to be logged here as **ADR-008** when sent. Disclosure does NOT happen earlier (premature) or later (forfeits transparency benefit).

**Reason:** Lokesh is an Anthropic Pioneer; the substrate runs on Claude (Code + Agent SDK + API). The default "stay quiet under pseudonym" forfeits potential amplification, early signal of policy/product changes, and risks relationship damage if Anthropic discovers it via third party. Transparency-with-context (pseudonymity-for-moonlighting reasons, here's a 1-page summary, happy to walk through it or keep building quietly) hedges both directions. **No upside cost** if they say "good luck"; real upside if they connect to customers / advise on Anthropic-Skills positioning / include in Pioneer demo days.

---

## ADR-009 (2026-05-10): Cloud-session plan-author reviews — 3 pre-gate + 1 ad-hoc

**Decision:** The cloud Claude Code session (Opus 4.7) that originated `PLAN.md` provides a 1-page plan-author-tier review at T-2 to each of the 3 bright-line gates (**2026-06-06, 2026-07-06, 2026-08-06**) plus one ad-hoc rescue review triggerable by operator. **Total: 4 reviews max across the 90-day window.** Triggered via `/plan-author-review` slash command from a fresh cloud Claude Code session in this repo (SessionStart hook auto-primes). Output is consumed by cc-main on local; operator + cc-main retain decision authority — cloud-session review never auto-merges.

**Reason:** cc-peer covers daily/weekly drift but shares local context with cc-main; assumptions calcify over 90 days. Plan-author-tier review brings stranger-context + intent-of-origin reasoning that cc-peer cannot reproduce — specifically, awareness of the 10 prior framings the plan was reacting to, so an 11th framing disguised as "scope clarification" is detectable. Cadence is gate-aligned to keep output decision-relevant; capped at 4 to prevent the compounding-thread interruption + parallel-mainline-writes failure mode the plan forbids in `## Parallelism vs compounding`. Shape is fixed (1 page, 4 sections: plan-vs-actual / drift signals / bright-line proximity / recommended actions); recommendations must be concrete (file path / commit / date / time-bound). Reference: `.claude/commands/plan-author-review.md`.

**Calendar:**
- **2026-06-06** (T-2 to W4 / Day-30 gate): pre-gate read on Track A paid Pro count + Track B waitlist + paid-post conversion → Outcome 1/2/3/4 recommendation
- **2026-07-06** (T-2 to W8 / Day-60 gate): pre-gate read on Track A paid Pro count vs ≥5 threshold (kill / continue)
- **2026-08-06** (T-2 to W12 / Day-90 gate): pre-gate read on success metrics across Track A, Track B, and career-capital lanes
- **Ad-hoc rescue (×1 max within 90 days, untimed):** triggered by Sunday journal flagging 11th-framing pull, OR operator-sensed ambiguity cc-peer can't resolve, OR a `PLAN.md ## Risks` item materializing in unexpected shape

**Failure mode to watch:** cloud-session reviews accumulating into a "we'll wait for cloud sign-off" pattern. **Mitigation:** hard cap at 4 sessions across 90 days; exceeding requires ADR amendment with cc-peer sign-off. If operator catches themselves wanting a 5th cloud review, the answer is to write a Sunday journal entry instead — the urge to seek external validation is itself signal worth examining locally.

---

*(Future ADRs append below this line. Format: `## ADR-NNN (YYYY-MM-DD): <one-line decision>` + Decision + Reason paragraphs.)*

---

## ADR-010 (2026-05-10): Pre-flight allowlist for cosmetic-known-noise

**Decision:** BOOTSTRAP.md §Pre-flight check #2 ("Any uncommitted changes in the repo? if yes, report and stop") is amended via this ADR to except a specific allowlist of paths from the stop condition. **Allowlist:** `.brain/ledger/*` (runtime auto-emit telemetry), `**/scratch/`, `**/scratch/*` (cross-lane scratch dirs under `mcp-server-nucleus/`), `docs/design/` (untracked design notes from other CC lanes), `mcp-server-nucleus/uv.lock` (peer's dep state drift on inactive branch). When `git status --short` shows ONLY paths matching the allowlist, pre-flight passes. Any non-allowlisted modification or untracked file still triggers the stop condition.

**Reason:** Day 0 (2026-05-10) pre-flight halted on six items, none authored by cc-main: `.brain/ledger/*` files re-dirty within minutes of any commit (auto-emitted by the running ledger system), scratch dirs + `docs/design/` contain other-CC-session WIP, and `uv.lock` reflects peer's dep work on a different branch. Strict interpretation of "no uncommitted changes" would either (a) force cc-main to commit cross-lane work (lane violation per `feedback_lokesh_not_gh_ops` + `feedback_finish_before_committing`), (b) require stash/skip-worktree workarounds every session (recurring chore that doesn't compound), or (c) gate Eidetic Works behind a multi-lane substrate cleanup that's out of W1 scope. The allowlist is narrow + named, distinguishes signal from noise, and preserves the original intent of the rule (catch UNINTENTIONAL drift authored by cc-main). If a noise path migrates to a real signal source (e.g., `docs/design/` becomes intentional), the allowlist is amended via subsequent ADR. Bootstrap text untouched; this ADR governs interpretation.

**Note on ADR numbering:** ADR-008 explicitly skipped — reserved for cc-peer's Pre-Day-1 pre-mortem per STATUS.md ## This week's targets ("Posted to DECISIONS.md as ADR-008"). ADR-009 already taken by Cloud-session plan-author reviews. Next free was ADR-010.

---

## ADR-011 (2026-05-10): Sub-agent registry — parallel-session default, subagent_type for cold-read tactical use

**Decision:** All three Opus 4.7 instances (cc-main + cc-peer + cc-tb running as parallel Claude Code sessions reachable via .brain/relay/) are committed to the Eidetic Works 90-day probe as their primary work for the duration. Nucleus-substrate work the parallel sessions were doing previously pauses for the 90-day window unless explicitly task-listed in the same probe (the substrate IS Eidetic Works at a deeper layer).

For each role in the BOOTSTRAP §Sub-agent registry:
- **Default mechanism = parallel persistent session** (warm Eidetic context, calibrates over 90 days)
- **subagent_type via Agent tool = tactical override** when structural cold-read is the feature: pre-mortems where bias-from-history is the concern, T-2 gate-decision drafts, plan-author rescue invocations

Cold-read is a deliberate exception, not the default. Calling the parallel session is the first move; spawning a subagent is the move when cold-context is what the task structurally needs.

Charter model-tier: cc-peer subagent charter (.claude/agents/cc-peer.md) amended from `model: sonnet` to `model: opus` so the structurally-cold-read tasks (pre-mortems, gate drafts) match the parallel-session tier. Other charters retain existing tier.

**Reason:** Original BOOTSTRAP §Sub-agent registry conflated mechanism with role. Day-0 surfaced the conflation — operator (Lokesh) correctly flagged that three Opus instances pointed at the same compounding thread is a stronger move than three Opus pointed at different threads. Cold-read concern is real but tactical, not architectural — solved by reaching for subagent_type spawn when needed, not by making it the default. The substrate work the parallel sessions were doing was Eidetic Works substrate one layer deeper; refocusing the parallel sessions on the product face accelerates the 90-day probe at the acceptable cost of pausing one layer of substrate work for 90 days. If Day-60 fires kill, substrate work resumes; if Day-90 ships, substrate work continues as the engine.

**Reference:** Bootstrap clarification incident 2026-05-10 (PR #314 mid-execution, Lokesh's "compounding move" critique). Did not consume ADR-009 ad-hoc rescue slot — informal clarification.

---

## ADR-008 (2026-05-10): W1-W4 most likely failure mode is capacity collapse, not technical failure

**Decision:** The single failure mode most likely to materialize before the Day-30 gate (2026-06-08) is **operator time-deficit compounding against a W1 plan that is structurally over-loaded for part-time hours.** The predicted failure sequence: W1 slips (daemon not shipped Day 7), W2 scope arrives anyway (compliance daemon), debt accumulates, Day-30 gate is reached with no shippable binary and therefore no paid conversions to measure — and the gate degenerates from a decision into a rationalization. Mitigation: declare and enforce a W1 scope triage rule now, before Day 1: if Day 4 benchmark is not passing by end-of-day Tuesday, immediately defer the MCP bridge (Day 6), the marketplace submission (Day 7), and the Track B interview schedule — keep only the daemon binary and one latency benchmark in scope for the gate.

**Reason:** Four evaluations, each pointing at the same root cause.

**(a) Part-time hours vs W1 scope.** The plan budgets "~12-15 hours over week 1" and lists nine Day-7 deliverables across two tracks: Go daemon scaffold + engram capture + retrieval benchmark + MCP bridge + daemon GitHub release + demo video + Distribution Officer first posts + Cursor/Windsurf marketplace submission + internal Axis pitch deck. Lokesh's realistic coding-review window at VP-day-job + family is 1-2 hours on weeknights, 3-4 hours on weekend mornings — 10-12 usable hours at the upper bound, with zero buffer for context-switch cost. "AI does most coding; Lokesh reviews" is true, but review of Go PRs from an unfamiliar codebase (Risk #11 in the plan itself) costs 30-45 minutes per PR, not 5. Nine deliverables in 12 hours is a plan for a long-weekend hackathon with a known codebase, not a cold Go project. The plan lists this risk and proposes a fallback (Bun/TypeScript), but the fallback is buried and not operationalized as a trigger-and-time-limit.

**(b) Cloudflare stack: one concrete showstopper.** D1 row limits (10M rows per database, 2GB storage per database) are fine for W1 scale; Workers CPU-time limit (50ms CPU per request, 30s wall-time) is fine for relay-and-respond patterns. The material gap: **Clerk's free tier requires a valid US phone number for OTP and has no India-region compliance declaration for data residency** — this is a non-issue for W1 (Cloudflare sync is deferred to W2-3) but becomes a blocker the moment Pro tier billing wires in W4 and real users authenticate. R2 egress pricing ($0.09/GB after the free tier) is benign at low scale. The actual W1 showstopper risk is simpler: `mattn/go-sqlite3` requires CGO, which means the "single binary" claim requires cross-compilation with a C toolchain — darwin-arm64 to linux-amd64 cross-compile with CGO is non-trivial and routinely breaks in CI. If it breaks on Day 3, debugging it eats the Day 4 and Day 5 slots.

**(c) Pseudonymity: defensible in W1-4, fragile by W4.** Cloudflare WHOIS privacy blocks casual lookup. The commit-email forensics risk is partially mitigated by the plan (per-repo `.gitconfig` override, forward-only). The real exposure is **Stripe seller verification**: Stripe requires a legal entity name, EIN/TIN, and bank account for payouts. Stripe Atlas issues a Delaware C-corp, which has a registered agent in Delaware — but the registered agent's client list is not public, and Delaware does not require the beneficial owner's name in public-facing documents at formation time (beneficial ownership is filed with FinCEN under BOIR, not public). So the Stripe/Atlas path is actually more defensible than the plan implies. The genuine gap is LinkedIn cross-reference: if the Eidetic Works GitHub org has commits with a newly-created committer identity but the content is unmistakably the same codebase as `mcp-server-nucleus` (same file structure, same variable names, same Python idioms), a motivated competitor or Axis compliance review can connect them. Pseudonymity buys time, not permanent cover.

**(d) <100ms P95 SLO: achievable in Go-only W1, uncertain once Python sidecar lands.** The Day-4 benchmark (Go SQLite WAL retrieval from 10K rows over a Unix domain socket) will comfortably hit P95 <100ms — UDS round-trip is sub-1ms, SQLite WAL indexed read is sub-5ms, Go net/http overhead is sub-2ms. The SLO risk emerges in Day 6 when the MCP bridge adds a hop: Go daemon → Python sidecar → Go daemon. If Python MCP server is not pooled (i.e., spawned fresh per request), CPython startup is 80-150ms on its own, blowing the SLO immediately. The plan says "MCP queries become snappy without rewriting MCP" but does not specify whether the Python sidecar is a persistent process or spawned per-call. This is not a W1 blocker if the bridge step is deferred, but the plan does not defer it — Day 6 is the bridge day, Day 7 is the demo. If the Python sidecar is cold-started, the benchmark in the README will not reflect the end-to-end latency the user actually experiences, which is a honesty problem and a future-churn problem when users measure it themselves.

**Core finding:** the capacity math (evaluation a) and the CGO cross-compile risk (evaluation b) are both pointing at the same Day-3/Day-4 crunch. The plan has no explicit triage rule for this scenario. A pre-committed triage rule — "if Day 4 is not green by 18:00 local, defer all W1 deliverables except daemon binary + benchmark" — prevents the rationalization cascade that turns a one-day slip into a four-week spiral. The bright-line at Day 30 holds regardless; this triage rule is about preserving the signal quality of the data that flows into that gate.

---

## ADR-012 (2026-05-10): Go MCP daemon hot path validated — P95 0.6-0.9ms on 10K-engram SQLite-WAL fixture

**Decision:** The Pre-Day-1 cc-tb spike (worktree-isolated, 6h time-boxed, per Prompt 0 step 1) validates Go + `mattn/go-sqlite3` + WAL mode as the W1 daemon hot path with two orders of magnitude of headroom under the 100ms P95 SLO. Bun + TypeScript fallback per PLAN.md Risk #11 + ADR-002 stays parked. W1 implementation proceeds in Go per the original Day-1-through-Day-7 schedule. Worktree at `.claude/worktrees/agent-a99923c8258077450` is scratch; architectural notes (CGO build flow, indexed retrieval pattern, WAL pragma defaults, batch-insert recommendation, MCP framing library still TBD) carry forward as design anchors but no spike code is harvested directly into mainline — W1 is a clean rebuild against `docs/specs/eidetic-daemon-w1.md`.

**Reason:** Three back-to-back runs on M-series Mac, 1000 requests each post-warmup, indexed `(surface, ts DESC)` retrieval over 10K-row engram fixture. **P95: 0.578 ms / 0.609 ms / 0.878 ms across three runs.** P50 ~67-494µs, P99 ~0.7-1.07 ms, max ~0.8-2.5 ms. ~110× under the 100ms SLO and ~1000× under the worst-case latency budget. Throughput ~13-14K req/s. The hot path is Go runtime overhead (JSON marshal, net/http), not SQLite — meaning further headroom exists if the JSON layer is replaced with binary or columnar serialization, but the current numbers are already so far under the SLO that no further work is warranted in W1. Architectural surprises flagged but not blocking: (a) Go is not preinstalled on a clean machine (`brew install go` + Xcode CLT prerequisite — add to W1 onboarding doc), (b) the spike implements MCP-handler-shape inline; a real W1 build needs either `mark3labs/mcp-go` library evaluation or hand-rolled JSON-RPC stdio framing as a Day-1 deliverable, (c) seed time is non-trivial (170-360ms for 10K-row insert in single transaction) — bulk-import flows should batch (one-row-per-event capture is unaffected). FTS5 + larger row counts not yet benchmarked; revisit if (a) row count >1M, (b) FTS5 enters the hot path, or (c) MCP framing library proves unworkable in Go.

**Reference:** Pre-Day-1 spike result (cc-tb worktree-isolated, 7-min runtime). Supersedes any prior latency uncertainty around ADR-002.

---

## ADR-013 (2026-05-10): W1 daemon spec — cold-read evaluation, conditionally achievable

**Decision:** The narrowed W1 scope (engram capture + retrieval + multi-surface mirror in Go, P95 <100ms SLO) is **achievable in 7 days at part-time hours, conditional on five operational guardrails being declared and enforced before Day 1 starts.** Without those guardrails, the most likely outcome is a 2-3 day slip into W2 driven by capture-side `fsnotify` rabbit-holing — not retrieval latency, not CGO. cc-tb's confirmed 0.6-0.9ms P95 (ADR-012) validates exactly one of nine W1 deliverables. The other eight are still unproven and three of them dominate the schedule risk. The spec as drafted is technically sound; the schedule as drafted is optimistic by ~30% under cc-peer's read.

**Reason:** Five independent concerns from a cold read of `docs/specs/eidetic-daemon-w1.md` and `STATUS.md ## This week's targets`, each pointing at a separate failure pathway.

**(1) cc-tb's P95 number proves retrieval, not W1.** ADR-012's 0.6-0.9ms is a benchmark of the SQL hot path on a synthetic 10K-row fixture under sequential request load. It validates Risk #1 (latency) decisively. It says nothing about: per-surface incremental parsers under burst writes, `fsnotify` event coalescing on macOS, launchd plist registration, install-script idempotency on a fresh laptop, GitHub release packaging, demo recording. With 110× headroom on the SLO, the Day-4 benchmark gate has stopped being a meaningful slip-detector — it cannot fail unless the implementation is grossly broken. **The Day-4 gate as currently written is now ceremonial.** Either retire it or replace it with a capture-correctness gate (see concern #4).

**(2) Capture-side concurrency is the real engineering risk.** Spec § 2.3 budgets <50ms file-write-to-row, but Cursor's session JSONL is multi-MB append-only with bursty writes during agent loops, and Claude Code's session JSONL writes are similarly chunked. `fsnotify` event coalescing on macOS (open question #2 in spec) is a known bug class — a single user keystroke can produce 0, 1, or N events depending on editor flush behavior. The spec acknowledges this but defers validation to "before Day 4." That puts validation on Day 3, which is also the CGO cross-compile day, which is also the schema-and-driver-wiring day. Day 3 is overloaded.

**(3) MCP framing library decision (Open Q #1) does not belong on Day 1.** Spec says "Decide Day 1 morning. Bench JSON-RPC overhead before committing." The daemon is an event-driven UDS HTTP server, not a JSON-RPC stdio MCP server. The two architectures have a real mismatch: `mark3labs/mcp-go` assumes stdio request-response, the daemon needs a long-lived UDS listener. Library evaluation typically takes 4-8 hours for an unfamiliar Go ecosystem; on Day 1 alongside spec finalization + 2 domain registrations + landing page deploy + cost playbook draft, this is the eraser that erases Day 1's daemon scaffold. **Recommend: defer MCP framing to its own deliverable post-W1; W1 daemon ships UDS-only with a `curl` smoke test.** PLAN.md Day 6 MCP-bridge work goes with it, consistent with the spec § 1 explicit-NOT list (which already excludes MCP bridge from binary v0).

**(4) Replace Day-4 gate with capture correctness, not retrieval P95.** If the SLO is structurally trivial (concern #1) and the real risk is capture (concern #2), the Day-4 hard checkpoint should be: **all four `fsnotify` integration tests green against real Cursor + Claude Code session fixtures captured under load** — not synthetic. ADR-008's triage rule ("if Day 4 not green by 18:00 local, defer Day 6 + Day 7 work") gets re-anchored on this gate. Retrieval P95 stays as a soft assertion in `bench_test.go` but is not the ship-blocker.

**(5) Day 1 capacity is unrealistic without an explicit marathon-burst declaration.** STATUS.md Day 1 (Sat 2026-05-11) lists: spec finalize + `eidetic.works` register + landing page v0 + cost playbook draft + `eidetic.app` register. ADR-008's capacity envelope is 3-4 hours on weekend mornings. Day 1 as scoped is a 6-8 hour day. Either the scope shrinks (drop `eidetic.app` Track B parallel-launch to Day 2 or W2), or PLAN.md § Calendar elasticity gets invoked explicitly with a marathon-burst entry in `STATUS.md ## Marathon-burst log` before Day 1 starts. Pretending Day 1 fits the normal envelope is the exact "rationalization cascade" ADR-008 names as the failure mode.

**Five guardrails for "achievable" verdict to hold:**

1. Day 1 is declared a marathon-burst (≥6h) **or** Track B `.app` work moves to W2.
2. Day 3 CGO darwin→linux cross-compile spike runs first thing; if broken by 14:00 local, accept darwin-only Day-7 release; flag in install.sh and README.
3. Day 4 gate replaced with capture-correctness on real session fixtures (not synthetic). Retrieval P95 stays as a `bench_test.go` assertion at 100ms threshold but with 110× headroom is not the ship-blocker.
4. MCP framing decision (spec Open Q #1) is deferred — not made on Day 1. Daemon ships UDS-only.
5. ADR-008 triage rule fires hard at Day-4 EOD: if capture correctness gate red, Day 6 (MCP bridge) + Day 7 (marketplace + Axis deck) are dropped without further deliberation. Pre-commit the rule before the slip is observed.

**Without these:** projected slip is 2-3 calendar days into W2, almost entirely on capture-side `fsnotify` debug. Retrieval and CGO are not the schedule risk; they're the spec's well-mitigated risks. The gap is in the spec's optimism about Day 1 capacity and the obsolete framing of the Day-4 gate.

**Out of cc-peer scope (escalate to cc-main, not decided here):** whether the marathon-burst is acceptable to declare on Day 1 (operator capacity call, not architectural). Whether `eidetic.app` Track B work survives W1 at all (strategy call). cc-peer's lane is the technical/structural read; the calendar trade-offs are cc-main's.

**Reference:** `docs/specs/eidetic-daemon-w1.md` @ `b3caa126`; ADR-008 capacity-collapse pre-mortem; ADR-012 cc-tb retrieval spike; PLAN.md § 7-Day Kickoff Sprint + § Risks #4/#11/#12/#13. Cold-read pass; no consultation with cc-main framing per cc-peer charter § Operating principles.

---

## ADR-014 (2026-05-11): Spike architectural notes worth carrying into W1 mainline build

**Decision:** Five architectural patterns from `.claude/worktrees/agent-a99923c8258077450/spike/main.go` are validated by the ADR-012 P95 result and should be inherited verbatim by the W1 mainline daemon; three load-bearing measurements are NOT in the spike and must be added as W1 deliverables before the Day-4 gate. Per ADR-012, no spike code is harvested directly — but the patterns below are the design anchors for the clean rebuild against `docs/specs/eidetic-daemon-w1.md`.

**Reason:** Independent read of the 223-LOC spike (cc-tb, post-pivot per ADR-011). The benchmark proved one specific shape (sequential-read, warm-cache, single-process, indexed retrieval over 10K rows). The patterns that produced 0.6-0.9ms P95 are reusable; the gaps are real.

**Carry forward into W1 mainline (5 patterns):**

1. **SQLite open-string pragmas** — `?_journal=WAL&_synchronous=NORMAL&_busy_timeout=5000&cache=shared`. WAL is non-negotiable (reader/writer concurrency); `synchronous=NORMAL` is the right durability/speed trade for engram capture (loss-window = last 1-2s of writes on power-loss, acceptable for an append-only audit-shaped store); `busy_timeout=5000ms` masks transient lock contention without escalating to lock-error handling in the hot path. Document the loss-window in `README.md` under "Durability" so power-loss surprise is preempted.

2. **Composite index `(surface, ts DESC)`** — covers the canonical retrieval pattern (per-surface, time-ordered, recent-first, LIMIT N). Confirmed via the benchmark: the entire hot path (parse → query → scan → marshal → respond) is dominated by Go-runtime overhead (json.Marshal, net/http allocation), not SQLite — meaning the index choice is correct, no further tuning needed at this row count.

3. **Connection-pool shape: `SetMaxOpenConns(1)` for writer, separate read-only pool for readers.** Spike uses single-conn. W1 mainline should split: one writer (single sql.DB, MaxOpenConns=1, owns all INSERTs) + read pool (separate sql.DB instances opened with `?mode=ro`, MaxOpenConns=4-8). This matches SQLite's fundamental "single writer, many readers" architecture and avoids the false-economy "database is locked" cascade the spike's single-conn pattern would hit under concurrent load.

4. **Prepared-statement batch insert for bulk paths** — spike's seed (10K rows in 170-360ms via single tx + prepared stmt) confirms the batching pattern. Realtime engram capture is one-row-at-a-time and unaffected, but **bulk-import** flows (rebuild from session JSONL backlog, mirror catch-up after offline window) must use this pattern, not row-by-row autocommit, or import time scales linearly with N.

5. **Cgo dependency (`mattn/go-sqlite3`) is the right call FOR W1, but flag the cross-compile + Tauri risk** — the spike uses cgo and clears the SLO with margin. The cost: cross-compilation darwin-arm64 → linux-amd64 → windows-amd64 requires a C toolchain on every target (or a CGO-enabled Docker buildx setup), which routinely breaks in CI (per cc-peer ADR-013 § evaluation b). For Tauri sidecar (W1 Day 4 spike), the pure-Go alternative `modernc.org/sqlite` should be benchmarked head-to-head: if it clears 100ms P95 with margin (it likely does, given 110× headroom), it eliminates the entire CGO cross-compile blast radius — at the cost of 2-5× per-query overhead which the SLO budget can absorb. **Recommendation:** Tauri spike (W1 Day 4) explicitly tests `modernc.org/sqlite` as the cross-compile-friendly fallback before mainline commits to `mattn/go-sqlite3` for distribution.

**Gaps in spike that W1 mainline must measure (3 deliverables):**

A. **Write P95** — spike measures READ only. Engram capture under burst-write load (Cursor agent loop emitting 50+ events/sec on long sessions) is structurally different. W1 deliverable: `bench_test.go` measures p50/p95/p99 of single-row INSERT under 100 req/s sustained for 60s. Pass-criterion: P95 <50ms (spec § 2.3).

B. **Cold P95** — spike runs 50 warm-up queries before measurement. Real daemon launches via launchd on user login, takes its first request from a cold page-cache. W1 deliverable: bench includes a cold-start path (open DB, immediately retrieve, no warm-up) — measure P95 of first 10 requests. Pass-criterion: P95 <500ms (10× the warm SLO is acceptable for cold).

C. **Concurrent P95** — spike is sequential. Real daemon receives concurrent retrievals from N surfaces (cursor + cowork + claude-code + windsurf + antigravity = up to 5 concurrent reads + 1 writer). W1 deliverable: bench fires 5 concurrent reader goroutines + 1 writer goroutine for 60s, measures p95 across all read responses. Pass-criterion: P95 <100ms under 5-reader contention.

**Architectural surprises NOT yet handled by spec § 1 or spec Open Q's:**

- **JSON marshal in hot path is not the bottleneck even at 100-engram × ~1KB-text response (~100KB output).** `encoding/json` clears P95 with margin. Spec should drop any "consider binary serialization" tangent — decision is made: stay with `encoding/json` until proven otherwise by a real workload, not a hypothetical.
- **Tag-filter retrieval is unindexed in the spike** — only `(surface, ts DESC)` is indexed. If W1 retrieval API adds `tag IN (...)` filters, current schema requires a full scan within the surface partition. If tag-filter is a Day-7 user-visible feature, schema must add `idx_tag_ts` or a dedicated `engram_tags` join table; this is a schema design decision that goes in `docs/specs/eidetic-daemon-w1.md` § Schema, not deferred.

**Out of scope (not what cc-tb is deciding here):**

- Whether the W1 timeline absorbs the three additional bench deliverables (A/B/C above) is a cc-main capacity call, not architectural.
- Whether to commit to `modernc.org/sqlite` for distribution before the Tauri spike runs is premature; the recommendation is to bench it during the spike, not switch sight-unseen.
- Whether to retain `encoding/json` long-term or move to a binary protocol for high-engram-count queries (>1K engrams/response) is a post-W1 question once real usage data exists.

**Reference:** `.claude/worktrees/agent-a99923c8258077450/spike/main.go` @ worktree-only (not for mainline harvest); ADR-012 P95 measurements (0.578 / 0.609 / 0.878 ms across 3 runs); `docs/specs/eidetic-daemon-w1.md` § 2.3 + § Open Questions; ADR-013 cc-peer guardrails (concerns #1, #4 inform gaps A and C above). Independent read pass per relay `relay_20260510_164028_7fcfc148` first deliverable; cc-tb spike-director lane per ADR-011.

---

## ADR-022 (2026-05-21): LinkedIn two-prong strategy + admin-identity behavioral firewall

**Context:** Distribution autopilot wiring (Buffer + growth-scheduler Worker) needs a documented stance on LinkedIn before any company-page admin work happens. Moonlighting risk is binding (PLAN.md:464 HARD KILL on personal-LinkedIn-Nucleus brand). Question raised mid-Buffer-setup 2026-05-21: real-Lokesh account admin vs burner. Ultraplan + cc-main cold-read independently; both passes converged on the same answer.

**Decision:** Two-pronged LinkedIn strategy. Real Lokesh account admins the Eidetic Works company page (burner accounts REJECTED). Behavioral firewall is the binding mechanism. Strategy documented in full at `docs/LINKEDIN_TWO_PRONGED.md`.

**Why real-account admin (rejecting burner):**
- LinkedIn TOS §8.2 prohibits duplicate accounts; detection via IP / device fingerprint + Buffer OAuth correlation = high probability.
- Failure mode if banned: BOTH burner + Eidetic Works company page deleted, no appeal. Worst-possible outcome (loses career-critical surface + brand surface simultaneously).
- LinkedIn does not publicly display company-page admins → the realistic moonlighting threat (Axis colleague stumbles onto the page) is already addressed by default. No burner needed.

**Binding constraint:** Behavioral firewall, not account-identity hiding. Specifically: no cross-follow, no like / comment / reshare from personal profile, no Experience listing of Eidetic Works, Activity Broadcasts OFF, separate Chrome profile for admin work, Buffer `BUFFER_PROFILE_LINKEDIN` secret must be company-page profile ID never personal.

**Status:** Prong A (Eidetic Works company page) traction-gated — deferred until first paid Pro signal from X. Prong B (personal Axis-career-hedge) active now, 1-2 posts/week.

**Reference:** `docs/LINKEDIN_TWO_PRONGED.md` (this commit); ultraplan + cc-main cross-validation transcript in 2026-05-21 session at `~/.claude/projects/-Users-lokeshgarg-ai-mvp-backend/`; `PLAN.md:433/464`; `memory/user_employment_context.md:7-15`; `.brain/thrive_april2026.md:760`. ADR-018 brand-LOCK (Eidetic Works) is the parent decision this implements. Future ADR-NNN if Axis disclosure compresses (per ADR-007 Day-30 disclosure plan) — this ADR-022 framework will need a revisit then.

**Out of scope (deferred):**
- Per-week posting cadence for Prong B beyond 1-2/week baseline
- Banker-network outreach list (Day-61+ activity, requires WebSearch-verified URLs at run time, no fabricated names)
- Company-page daily cadence specifics (Prong A is traction-gated; cadence design happens post-gate)

**Note on numbering:** Local branch `release/v1.3.0` DECISIONS.md jumps from ADR-014 directly to this ADR-022. ADRs 015-021 exist on other branches (verified via `git log --all`) but haven't been merged into this branch. Numbering gap is a branch-state artifact, not a content gap; resolves on next merge.
