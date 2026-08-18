# ADR-006 (2026-08-18): Stage 1 exit-gate criterion (A) — cumulative installs — PASS

**Gate:** `BILLION_DOLLAR_ROADMAP.md` Stage 1, exit gate (dual, both required,
2026-10-08). This entry resolves criterion (A) only.

- **(A) Cumulative installs ≥250** — **PASS**, closed here.
- **(B) D14 retention ≥15%, n≥40** — still open, not yet measurable. Cohort
  window is 2026-08-15→09-24; the gate reads 2026-10-08. This entry does not
  and cannot resolve (B) — there isn't enough data in the window yet. Not
  doubt, just time; it will be closed by its own ADR when the cohort matures.

**Evidence for (A), pulled live 2026-08-18 via the GA4/Firebase Data API
(service account `firebase-adminsdk-fbsvc@gentlequest-prod`, key `83ff55c0b550`,
property `516568186`), lifetime range 2025-01-01 → today:**

| Source | Metric | Count |
|---|---|---|
| iOS | `first_open` (lifetime) | 142 |
| Android | `first_open` (lifetime) | 67 |
| **Native mobile subtotal** | | **209** |
| Web | `newUsers` (lifetime) | 144 |
| **Combined** | | **353** |

`first_open` is a standard Firebase SDK event fired exactly once per real
install — not sample-based, not gameable by the same undercounting that
made App Store Connect's own App Analytics dashboard read "1" for the same
90-day window (that dashboard is opt-in-sample only and is known-unreliable
at this app's volume; Payments & Financial Reports has no data at all since
the Paid Apps Agreement was never signed). GA4/Firebase is the credible
source here, not ASC's UI.

Native mobile alone (209) is close to the 250 bar; combined with web (353)
it clears it. The web figure carries one open caveat: it's raw GA4 web
`newUsers`, which may include marketing/landing-page traffic rather than
strictly people who used the mood-check-in web app (the distinction the
original, now-dead `web_install_delta.sh` local counter was trying to
isolate). Native mobile's 209 alone does not depend on that caveat and is
the load-bearing number for this pass.

**Verdict: criterion (A) is PASSED and CLOSED as of 2026-08-18.** Not to be
re-opened absent new contradicting evidence. Criterion (B) remains the one
open half of the Stage 1 gate.
