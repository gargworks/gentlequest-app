# GentleQuest v1.4.0 Product Requirements Document (PRD) DRAFT

## Reference Designs Index
- **[R1D10]**: Regional Compliance gating matrix and resource cards.
- **[R1D11-A]**: Crisis Keyword Override (200ms swap to 988 surface).
- **[R1D11-B]**: MDM/School Device Block special framing.

## Dependency Note
**Gated on v1.3.0 Store Acceptance**: All v1.4.0 work is contingent upon Apple/Google approving the v1.3.0 submission. If rejected, rejection-remediation items will preempt this scope.

## 1. Goal
Achieve a "stable release for months" milestone. This requires sealing all critical compliance/safety gaps (ComplianceGuard), finalizing core app configuration (package names, universal links) before the first store upload locks them in, and addressing key dogfood UX gaps (chat latency, onboarding, emergency response benchmarked against Wysa).

## 2. Ranked Scope Shortlist

### BLOCKERS (Must-haves for stable V1 rollout)

**1. ComplianceGuard: Crisis Keyword Override (R1D11-A)**
- **Severity:** BLOCKER (Safety/Liability)
- **Effort:** M
- **Description:** Implement a 200ms transition to a 988/Crisis surface if self-harm keywords are detected during onboarding or chat. 
- **Dependencies:** Keyword detection heuristic/API.

**2. Regional Compliance Matrix & Gating (R1D10)**
- **Severity:** BLOCKER
- **Effort:** M
- **Description:** Replace hardcoded Illinois block with a dynamic template `"{state}"`. Implement regional resource cards (e.g., NAMI Illinois, Crisis Text Line) and decide on international vs. US-only release. 
- **Dependencies:** Legal matrix research (HIPAA, GDPR, DPDP 2023).

**3. Package Name & Universal Links (AASA) Finalization**
- **Severity:** BLOCKER (Immutable after first upload)
- **Effort:** S
- **Description:** Lock decision in — KEEP `app.gentlequest.www` (operator-confirmed 2026-05-31; immutable post-first-upload). Validate AASA + assetlinks 200 OK on `gentlequest.app` + add path exclusions to prevent catch-all hijacking `/privacy`, `/terms`.
- **Dependencies:** Domain DNS and Render static routing config.

*(Blocker Totals: 1 Small, 2 Medium)*

### HIGH (Strongly recommended for "stable for months" goal)

**4. Wysa Benchmark UX Parity: Chat Latency**
- **Severity:** HIGH
- **Effort:** M
- **Description:** Dogfood signals (e.g. ledger `evt-1768824156-eb31efb0` manual benchmark) indicate chat latency is a UX gap vs competitors like Wysa. Optimize websocket/polling or implement optimistic UI updates to make chat feel instant.
- **Dependencies:** Backend response time audit.

**5. Crisis Resource Localization (Medium #6 from Audit)**
- **Severity:** HIGH
- **Effort:** M
- **Description:** Current crisis resources (988, JED, Teen Line) are US-only. Must explicitly define localized crisis lines for UK, India, EU, and Canada.
- **Dependencies:** Regional Compliance Matrix.

**6. App Store Review Context (Medium #5 from Audit)**
- **Severity:** HIGH
- **Effort:** S
- **Description:** Prepare Review Notes explaining that location tracking is strictly for regulatory eligibility state-gating, to prevent App Review rejections from out-of-state reviewers.
- **Dependencies:** None.

*(High Totals: 1 Small, 2 Medium)*

### MEDIUM (Hygiene & Polish)

**7. ComplianceGuard: MDM/School Device Block (R1D11-B)**
- **Severity:** MEDIUM
- **Effort:** M
- **Description:** Special framing for managed devices to avoid privacy risks on school/corporate profiles.
- **Dependencies:** MDM detection plugin/service.

**8. iPad Support (Blocker #1 from Audit)**
- **Severity:** MEDIUM
- **Effort:** L
- **Description:** `TARGETED_DEVICE_FAMILY` was restricted to iPhone (1) for v1.3.0. Re-enable iPad support (1,2) and generate 13"/12.9" screenshots.
- **Dependencies:** UI responsiveness audit for tablet form factor.

**9. Wysa Benchmark UX Parity: Onboarding**
- **Severity:** MEDIUM
- **Effort:** S/M
- **Description:** Streamline the onboarding flow based on dogfood signals (ledger `evt-1768824156-eb31efb0`) comparing the experience to Wysa's frictionless start.
- **Dependencies:** None.

*(Medium Totals: 1 Small/Medium, 1 Medium, 1 Large)*

## 3. Out-of-Scope (What v1.4.0 will NOT include)
- Path B Dockerfile retry.
- GentleQuest landing page static site auto-deploy fixes.
- Payments and monetization infrastructure.
- Additional new clinical screening flows.
