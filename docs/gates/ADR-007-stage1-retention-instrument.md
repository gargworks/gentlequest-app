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
