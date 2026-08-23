# ADR-007 (2026-08-22): Stage 1 gate criterion (B) — native D14 retention instrument

**Gate:** `BILLION_DOLLAR_ROADMAP.md` Stage 1, exit-gate criterion (B):
**D14 retention ≥ 15% with n ≥ 40**. This ADR records the canonical
measurement instrument for that criterion.

## Decisions

1. **Canonical population is native iOS + Android only.**
   - Mobile app users are measured by the Firebase/GA4 SDK.
   - Web traffic is reported under `excluded_web` with reason
     `unqualified_marketing_mix` until the web app itself has a
     distinguishable analytics surface; it must not enter the verdict.

2. **Evidence is produced and persisted by the production backend scheduler.**
   - The existing 08:00 UTC `funnel_scheduler` attaches a `retention_gate`
     document to each `FunnelSnapshot.snapshot_data` row.
   - `metrics/d14_cohort_ga4.py` is the single shared collector/evaluator.
   - No new database table, migration, Cloudflare Worker, or marketing pipeline
     is required.

3. **Cohort math is offset-specific and explicit.**
   - D1, D7, and D14 each use only their offset-eligible subcohort:
     `firstSessionDate <= min(gate_end, report_day - offset)`.
   - Each offset reports its own `eligible_n`, `returned`, and `rate`.
   - Total arrivals are reported separately as `native.total_n`; the verdict
     uses the D14 offset-eligible count, never the blended total.

4. **Canonical window and observation cutoffs.**
   - Acquisition window: **2026-08-15 → 2026-09-24**.
   - Latest complete analytics day (`report_day`): the day before the run.
   - The final cohort's D14 calendar day is **2026-10-08** (Sep-24 + 14).
   - First complete read: **2026-10-09 08:00 UTC**.
   - Until `report_day >= 2026-10-08`, the verdict is `insufficient/not_mature`
     regardless of provisional D14 numbers.

5. **Credentials are scoped and never checked in.**
   - Resolution order: `GQ_GA_SA_JSON` (Render inline), `GQ_GA_SA_PATH`
     (resolver-managed file), `GOOGLE_APPLICATION_CREDENTIALS` / ADC with
     explicit `analytics.readonly` scope.
   - The legacy `secret/gentlequest-prod-sa.json` path is no longer used.

6. **Failure modes are persisted, not silent.**
   - Missing/malformed credentials, auth failures, permission errors, upstream
     unavailability, and in-window immaturity all produce a `retention_gate`
     row with a named `status`/`reason`.
   - A GA4 failure never blocks the ordinary funnel snapshot from committing.

## Verification

- Local CLI:
  ```bash
  uv run --python 3.11 --with-requirements requirements.txt \
    python metrics/d14_cohort_ga4.py --start 2026-08-15 --end 2026-09-24 --json
  ```
- Live history:
  ```
  GET /api/metrics/funnel/history?limit=1
  ```
  Expected: `freshness.status` of `ok`, `freshness.retention_gate_status` of
  `insufficient` with `reason=not_mature` before 2026-10-09, then `pass`,
  `fail`, or `insufficient/min_n` once the window matures.

## References

- `metrics/d14_cohort_ga4.py` — shared collector/evaluator.
- `scheduler/funnel_scheduler.py` — attaches `retention_gate` to daily snapshots.
- `routes/analytics_routes.py` — exposes freshness in `/api/metrics/funnel/history`.
- ADR-006 — already closed criterion (A); this ADR does not reopen it.

---

## Amendment — 2026-08-23: the instrument has no data source

Appended, not merged into the decisions above: those record what was ratified
and should stay as written. This records what was found to be true afterwards.

### The omission that caused this

**This ADR never named an authoritative GA4 property or GCP project.** It fixed
the population, the producer, the cohort maths, the window, the credential
*order* and the failure taxonomy — everything except *which property to query*.
That was left to a hardcoded `DEFAULT_PROPERTY_ID` in
`metrics/d14_cohort_ga4.py`. A constant nobody ratified is a constant nobody
re-checks, and it silently went stale.

**Any future gate ADR must name its data source explicitly.** An instrument
specified without one is specified without the only thing that determines
whether it can produce a number at all.

### What is actually true as of 2026-08-23

The gate cannot return a verdict, and no permission grant will change that.
Five findings, each verified directly rather than inferred:

1. **The app has no GA4 property.** It moved to Firebase project
   `gentlequestapp` (315814630048) on 2026-06-03 (commit `74c33128`), and that
   project has no linked GA4 property: Firebase `analyticsDetails` returns 404,
   its `resources` block contains only `hostingSite`, `google-services.json`
   has no `analytics_service`, `GoogleService-Info.plist` has
   `IS_ANALYTICS_ENABLED=false`, and the web bundle's `measurementId` is null.
   The GA4 "All accounts" picker for the owning user lists exactly one
   property — the old one.
2. **`DEFAULT_PROPERTY_ID = 516568186` belongs to the abandoned project**
   (`gentlequest-prod`, 680543456536). It still receives landing-page web
   traffic via `G-Z4Z92EJ3DV`, which is why it looks alive; its native app
   versions are frozen at 1.3.1 while the app ships 1.7.0.
3. **The service-account key is revoked.** `secret/gentlequest-prod-sa.json`
   (`firebase-adminsdk-fbsvc@gentlequest-prod.iam.gserviceaccount.com`) fails
   with `invalid_grant: Invalid JWT Signature` — dead credential, not a
   permissions problem. The SA belongs to the project whose **ID** is
   `gentlequest-prod` (number 680543456536). Note that a *different* project,
   ID `gen-lang-client-0814369801` (number 89695193768), carries
   "gentlequest-prod" as its **display name** and is the one the release
   toolchain uses. Three projects answer to that name; cite the project number,
   never the name. See the note in `docs/infra/protocols/NUCLEUS_OPERATIONS_GUIDE.md`.
4. **The collector has not run since 2026-08-11.** `com.gentlequest.analytics-pull`
   was disabled that day and recorded as "replaced by daemon_orchestrator";
   the replacement was a `pass`, behind a scheduling condition that could never
   be true. Fixed 2026-08-23 to fail loudly instead of silently.
5. **Production never had GA credentials at all.** `render.yaml` defines no
   `GQ_GA_PROPERTY_ID`, `GQ_GA_SA_JSON` or `GQ_GA_SA_PATH`, so the hosted path
   falls through to ADC and returns `permission_denied`. It has not regressed;
   it was never wired. Historical pulls were always local.

### Consequence for the window

Decision 4 sets the cohort window to **2026-08-15 → 2026-09-24**, first
complete read 2026-10-09. **No native telemetry exists for any part of that
window and none can be backfilled** — collection stopped on 2026-06-03.

The honest state of this gate is therefore INSUFFICIENT for structural reasons,
not immaturity, and it should not be reported as `not_mature`: that reason
implies data is accruing. Nothing is accruing.

Restoring it requires, in order: create and link a GA4 property to
`gentlequestapp`; re-run `flutterfire configure` so the app configs carry
analytics and enable it on iOS; **ship a build** (telemetry resumes only from
that release forward); issue a fresh service-account key; grant it on the new
property; set `GQ_GA_PROPERTY_ID`. The earliest honest D14 read is 14 days
after that build reaches users — which is a new window, and a decision for the
operator rather than something this ADR can assert.
