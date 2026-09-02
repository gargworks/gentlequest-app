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

---

## Second amendment — 2026-08-27: the instrument is restored; the window is not

Appended per the same rule as the first amendment: the ratified decisions and
the first amendment stand as written; this records what changed on 2026-08-27.

### What was restored (all verified by running the instrument, not by claim)

1. GA4 property **551876340** created and linked to Firebase project
   `gentlequestapp` (315814630048). Account 406219488. Web stream
   `G-MBBHN4PT39`; native streams for both Android apps and iOS.
   Data-sharing settings: all optional sharing declined.
2. Service account `firebase-adminsdk-fbsvc@gentlequestapp.iam.gserviceaccount.com`
   granted Viewer on the property; fresh key issued; the **Google Analytics
   Data API had never been enabled on the project** and was enabled — the raw
   PERMISSION_DENIED named the disabled service, which no amount of granting
   would have fixed.
3. Production (Render srv-d2r3i1fdiees73dqtov0) now carries `GQ_GA_PROPERTY_ID`
   and `GQ_GA_SA_JSON`. The hardcoded default in `metrics/d14_cohort_ga4.py`
   now names 551876340, with the old 516568186 documented as the
   wrong-population trap it was.
4. App builds carrying collection shipped 2026-08-27: **1.7.2+26082702** live
   on Play production and internal; iOS submitted for App Store review
   (auto-release). Collection is gated at the SDK level on Anonymity Mode,
   closing a latent gap where automatic events would have violated the shipped
   privacy promise.
5. The instrument's verdict moved from `error/permission_denied` to
   `insufficient/not_mature` — its first honest verdict since 2026-06-03.
   Production's next scheduled snapshot (08:00 UTC) will carry it.

### What is NOT restored, and cannot be

The ratified window (2026-08-15 → 2026-09-24) has no native data for its first
12 days and never will. Telemetry begins at the 1.7.2 install base, 2026-08-27
onward. Any D14 number computed over the ratified window mixes a dark period
into the denominator.

### Open governance decision — surfaced, not resolved here

Two live documents disagree about this exact scenario:

- `BILLION_DOLLAR_ROADMAP.md` (entry precondition): a retention pipeline not
  verified by **2026-08-15** auto-scores clause (B) **FAILED** — no exception.
- This ADR's first amendment: the honest state is **INSUFFICIENT for
  structural reasons**, distinct from a measured failure.

The roadmap's own middle-band clause allows ONE automatic 4-week extension to
**2026-11-05**. Whether to (a) score (B) FAILED per the letter of the roadmap,
(b) treat it as INSUFFICIENT-structural and restart the window at 2026-08-27
(making the earliest complete D14 read ~2026-10-10, inside the extension
window), or (c) something else, is the plan-author's call and needs its own
ADR. This amendment deliberately does not choose.

---

## Pointer — 2026-09-02: the open decision above has been taken up

Appended per the same append-only rule. Nothing above is altered.

`ADR-008-stage1-criterion-b-window-restart.md` rules on the open governance
decision recorded in the section above. It chooses **(b)**: criterion (B) is
scored INSUFFICIENT-structural, the acquisition window restarts at **2026-08-27**
(new window 2026-08-27 → 2026-10-22), and the roadmap's single 4-week extension
to **2026-11-05** is invoked.

ADR-008 is **PROPOSED, not ratified** as of this pointer. Until the operator
ratifies it, the window ratified in this document (2026-08-15 → 2026-09-24)
remains the one of record, and the disagreement noted above remains live.
