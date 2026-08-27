# GentleQuest — The Billion-Dollar Roadmap (deterministic, gate-funded)

**Date:** 2026-07-08 · **Status:** DRAFT for operator review — uncommitted, not yet an ADR
**Provenance:** 28-agent Fable-5 ultracode run (`wf_239a65a2-51d`): 6 grounding auditors (repo/strategy/traction/comparables/channels/rails) → 3 independent roadmap architects (viral-PLG, community-network, platform-B2B2C) → 3-lens judge panel → unified synthesis → 12 adversarial per-gate refutations + 18-gap completeness critique. Every gate below is post-fix: the original synthesis had all 12 verify checks return BROKEN, and the fixes are applied inline.
**Relationship to existing decisions:** ADR-005 (Aug-8 gate) is Stage 0 verbatim — untouched, no re-litigation. ADR-006 (six-month plan) remains the operating contract through Stage 2; one amendment is proposed (Gate-6 install number) and flagged in §9. This document extends beyond ADR-006's horizon and binds nothing until adopted by ADR.

---

## 1. The verdict up front

Three sentences of truth before any ambition:

1. **Stage 0 is the most probable death of this roadmap and nothing here changes that.** All three ADR-005 criteria sit at 0/3 with 31 days left (web installs flat at 11 for 8 straight days; non-direct users 1/20; zero recorded human voice). The roadmap honors the freeze if it fires.
2. **Bootstrap-only honestly ceilings at Finch-class (~$30–40M ARR ≈ $150–300M outcome).** The self-funded growth loop's physical ceiling is `g = reinvest_rate/payback − churn` ≈ 8–12%/month. The $1B endpoint requires external capital after unit economics are proven (Stage 5, Track F). This roadmap states that instead of hiding it in a 33x hand-wave — which is exactly what the adversarial pass caught the first draft doing.
3. **Every stage is funded by the proceeds of the one before it, every gate is a formula over a named artifact, and every kill is written as an ADR** so nothing can be quietly re-litigated in either direction.

## 2. Ground truth — 2026-07-08 (verified by repo audit, not vibes)

| Fact | Value | Source |
|---|---|---|
| Shipped version | **v1.5.0+26070308 — SHIPPED 2026-07-03** (Play live, iOS in Apple review). Body doubling, low-stim quiet mode, ADHD onboarding are IN it. | `origin/main` pubspec via gh api. *(The workflow's repo auditor read the stale live-checkout branch and concluded "not shipped" — corrected here.)* |
| ASO wedge | Subtitle "Body doubling, no streaks" + Play short description **already applied** (2026-07-03). Title change ("ADHD Companion") **deferred by operator** — no "ADHD" in visible copy this cycle. Keyword-lag clock started ~Jul 3. | Release session record; operator decision 2026-07-04 |
| Cumulative installs | Android 12 + iOS 16 + web 11 ≈ **39** | `funnel_snapshot.log` 2026-07-08 |
| GA4 90d | 184 active users, 26.6% engagement; **7-day actives = 2** (−83% w/w); non-direct = **1/20** | `metrics/analytics_latest.json` |
| Geography / platform | India 142 vs US 26; iOS 155 vs Android 17 | GA4 90d |
| Monetization | **Zero IAP code** anywhere (grep-verified). Free forever, $0 revenue. | repo grep |
| Retention | **Never measured.** No D1/D7/D30 cohort has ever been computed. | ground:traction |
| Backend | Single Flask/Postgres monolith; abandoned Cloud Run scaffolding exists unverified | repo audit |
| Known landmines | Journal privacy contradiction ("never synced" vs live `/api/journal` persistence); feedback widget writes local-only, cannot transmit; gate artifact `funnel_snapshot.log` is Mac-local (SPOF) | SIX_MONTH_PLAN.md 3c; repo audit |
| Channel ceiling (grounded) | ASO 5–30/wk building + SEO 2–15/wk + faceless video 0–5/wk ≈ **~50 installs/wk best case at maturity** | market:channels |
| Category | ADHD apps ≈ $1.9–2.2B (2025–26), 15–17% CAGR → $6.7–7.5B by 2033. Finch ≈ $30–40M ARR bootstrapped (the category's proven ceiling for single-player); its real engine was **paid** TikTok/Meta. Focusmate's 3-free-sessions/week paywall is the only grounded willingness-to-pay signal for body doubling. | market:comparables |

## 3. Thesis and wedge

**Thesis:** Run the only playbook a $0-budget, pseudonymous, moonlighting, fleet-executed founder can actually execute — the viral/PLG consumer skeleton (Finch's verified same-category path: attachment loop → faceless product-native distribution → store-rail freemium → proceeds-funded paid ads) — hardened with a body-doubling network layer as a **non-load-bearing** defensibility graft (it degrades to solo instead of killing the company), and with epistemic guardrails: no scale arithmetic is trusted until Stage 3 measures real ARPU/conversion; unmeasurable = FAILED, always; every kill and every pass is an ADR.

**Wedge:** *"Body doubling, no streaks"* — the streak-app-refugee wedge. Rising, low-competition search term that Finch/Inflow/Tiimo don't own in store search; paying demand externally proven (Focusmate paywalls it; Flow Club runs 2,000+ sessions/week); and GentleQuest's anti-streak, no-guilt identity is the exact opposite of every habit app ADHD users bounce off. The wedge copy is **already live** (subtitle + short description, shipped with v1.5.0).

## 4. The billion math (corrected)

Backward from the endpoint: **$1B ≈ $100–150M ARR** at consumer-subscription multiples.

- **Payers:** $100M ARR ÷ blended net ARPU **$45–60/yr** ≈ **1.7–2.2M paying subscribers**. ARPU band is India-weighted and commission-blended (30% first-year Apple / 15% after; the 15% small-business rate lapses above $1M/yr proceeds — the first draft ran 15% to the endgame and was wrong).
- **Users:** at 2–4% freemium conversion → 45–110M cumulative registered; ~8–12M MAU at the D30 ≥15% bar.
- **Market clearance:** $100M ARR = 1.3–2.2% of the projected 2033 category — only ~3x what Finch already achieved bootstrapped, single-player.
- **Calibration rule (blocking):** the grounding contains zero real ARPU/conversion comparables for THIS audience. Stage 3 exists to measure them; its calibration ADR re-derives this chain before a dollar of Stage-4 spend. Planning numbers above are bands, not commitments.
- **The physical ceiling, stated:** self-funded growth = `reinvest_rate/payback_months − monthly_churn` ≈ 8–12%/mo ≈ 2.5–4x/yr. That reaches ~$1–3M ARR by 2030 without capital. Track F (raise at Stage 5, on proven payback, through the incorporated entity) is what buys the 2.15x/yr for three more years to $100M. Track B (bootstrap) is the honorable fallback and is priced at Finch-class.

## 5. Cross-stage invariants (apply to every stage)

1. **Archived counting scripts:** every gate metric has a committed script/SQL in `~/gentlequest/metrics/` BEFORE its measurement window opens. Two readers run the same script; disagreement is impossible by construction.
2. **Unmeasurable = FAILED.** If instrumentation isn't live and test-verified by its named deadline, the clause it measures scores FAILED — never "extend to find out."
3. **Instrumentation ships before the cohort it measures** — as an entry precondition to the stage, not a work item inside it.
4. **Every kill and pass is an ADR** in `~/gentlequest/docs/ADRS.md`. No quiet re-litigation, no partial credit, no founder's-call escape hatches: every kill partition covers the full outcome space.
5. **Spend governor (Stage 4+):** **monthly** ad spend ≤ **65% of trailing-30-day bank-COLLECTED proceeds** (not reported — collected; the 35% holdback covers Indian advance tax + the 30–60-day store payout lag). Enforced by committed script. External cash burn = ₹0 by construction. *(First draft said "weekly ≤ trailing-30d," which literally authorized 4.3x monthly burn — fixed.)*
6. **Ship-gates once measurable:** D30 ≥15% and Sean-Ellis ≥40% (instrumented in-app before Stage 5, or struck) are rollback-enforced on every release from the moment they can be computed.
7. **Gate artifacts are not Mac-local:** `funnel_snapshot.log` and all counting inputs get a daily off-Mac copy (repo-committed or OCI) starting Stage 0 — the measurement apparatus currently shares a single point of failure with the founder's laptop.
8. **Competitor sensor:** weekly agent-run keyword-rank watch ("body doubling", "ADHD companion") + incumbent feature-watch (Finch/Inflow/Tiimo/Calm) from Stage 0. Free, automated, feeds every gate review.
9. **Pseudonymity ratchet:** no step creates public identity surface before its named unlock. The trader/seller-name problem (§9, decision 3) must be solved before any paywall ships.

---

## 6. The gate ladder

### Stage 0 — Prove Anyone Cares · 2026-07-08 → 2026-08-08 (ADR-005, committed)

**Objective:** Generate the first externally-verifiable demand signal before the committed freeze date. Declared primary path: **criterion (iii), human voice** — the adversarial pass proved (i) is arithmetically near-unreachable in-window (web installs flat at 11; ASO moves *store* installs on a 2–4-week lag and doesn't feed the web-install line at all) and (ii) requires 19x growth of a segment currently at 1.

**Exit gate (verbatim ADR-005, deadline 2026-08-08):** 4+/day web installs sustained 3 consecutive days, OR ≥20 non-direct GA4 users, OR any unprompted human voice. Measurement: (i) day-over-day deltas in `funnel_snapshot.log`; (ii) non-"(direct)" row sum in `analytics_latest.json` acquisition_90d; (iii) a deterministic human-voice ledger — admissible sources enumerated (ASC review row, Play review row, feedback-backend table row, inbound email to the product inbox, social-post URL), each entry timestamped + archived in `marketing/OPS_LOG.md`. All three counting scripts committed to `~/gentlequest/metrics/` in week 1.

**Kill:** none of the three by 2026-08-08 → freeze to portfolio mode per ADR-005, closing ADR written. No extension, no partial credit.

**Work (re-sequenced by verify pass — instrumentation FIRST):**
- ~~Build and submit v1.5.0~~ **DONE — shipped 2026-07-03**, ahead of the scope doc's Aug-8 target. iOS approval pending (one prior rejection on record; buffer already banked).
- **Feedback widget wired to backend, live + test-verified by 2026-07-18 — BLOCKING** before any traffic push. Until verified, an in-app human voice is physically uncapturable. (ADR-005-sanctioned task.)
- **UTM-tag every running surface** (blog daily posts, YT chain, X/Buffer queue) in week 1 — 183/184 GA4 users are "(direct)"; criterion (ii) literally cannot register without tagged links. Redirect content topics to the body-doubling wedge.
- **Creator barter blitz, resized to the lottery it carries: 80–120 ADHD nano/micro creators** (not 30–50), all outreach sent in week 1 to respect the 2–4-week reply lag. AI fleet drafts; founder sends from the product inbox in one bundled session. This is the highest-probability human-voice source.
- **Journal privacy fix** ("stays on your device" vs live server persistence) — trust-fatal for a mental-health brand, precondition for every later traffic push — **plus a store privacy-declaration audit** (Play Data Safety form + Apple nutrition labels vs actual `/api/journal` behavior; a misdeclaration is a store-removal offense independent of the in-app copy). [critic fix]
- **Off-Mac backup of gate artifacts** (daily `funnel_snapshot.log` copy) — the exit gate currently reads a file that dies with the laptop. [critic fix]
- ASO: keyword-lag clock already running on the shipped subtitle. Title decision stays with operator (§9). ASO is a Stage-1 store-install lever, not a Stage-0 web-install lever — planned accordingly.

**Unlocks:** continuation under ADR-006 — agent-labor investment in Stage 1, ~2h/week founder budget, $0 cash.

---

### Stage 1 — Build the Creature, Prove Attachment · 2026-08-09 → 2026-10-08

**Objective:** Ship the emotional-attachment core loop (a companion that grows with gentle check-ins and never punishes absence) and gate on retention, not raw installs. **Live multiplayer is CUT from this stage** [verify fix] — solo body doubling already shipped in v1.5.0; greenfield real-time multiplayer on a Flask monolith with bus-factor 1, in parallel with the companion build, was the capacity break the judges flagged.

**Entry precondition (not a work item):** retention pipeline (Firebase BigQuery export, pinned cohort query committed as `metrics/d14_cohort.sql`) verified live on a seeded test cohort **by 2026-08-15**, else clause (B) auto-scores FAILED.

**Exit gate (dual, both required, 2026-10-08):**
- **(A)** Cumulative installs (Play Console + App Store Connect + GA4 web, summed on the 2026-10-08 `funnel_snapshot.log` line) **≥250**. *(First draft said 500 — 461 net new in 8 weeks against a ~50/wk best-case channel ceiling; contradicted its own kill band. Re-based channel-honest.)*
- **(B)** **D14 retention ≥15%** on the 2026-08-15→09-24 first_open cohort, **n≥40**; n<40 = FAILED. *(First draft gated D30 on the September cohort — temporally impossible: a Sept-24 first-open has no D30 by Oct 8. D14 is computable; D30 ≥10% on the Aug–Sep cohort is read 2026-11-08 as a deferred confirmation that arms the Stage-2 ship-gates.)*

**Kill (full partition):** installs <100 OR D14 <7% (n≥40) → freeze ADR. Middle band (100–249 installs, or D14 in [7%,15%), or n<40 with installs ≥100) → ONE automatic 4-week extension to 2026-11-05, identical gate; second miss → freeze ADR.

**Work:** v1.6 companion loop (no streaks — it never dies, decays, or shames), Apple submission by 2026-09-15 to bank review buffer; shareable-artifact generator (mood-weather cards, session recaps, watermarked + UTM deep links); creator gifting 20+/month sustained; ASO variant rotation against Play search-term impressions on the 2–4-week cycle.

**Unlocks:** Stage-2 share-loop surface + IAP scaffolding behind a feature flag; D30/Sean-Ellis ship-gate regime arms as instrumentation matures. Still $0.

---

### Stage 2 — Prove the Loop · 2026-10-09 → 2027-01-08

**Objective:** Make the product its own distribution channel and gate on **loop quality, not a round number**. *(First draft kept the six-month plan's 10,000-install figure; grounded channel math undershoots it 7–14x, and its own tripwire projected landing inside its own kill band — a gate designed to fail. Re-based; requires an ADR-006 amendment, §9 decision 2.)*

**Exit gate (dual, 2027-01-08):**
- **(A) Share-loop thesis:** ≥10% of December-2026 new registrations carry share-artifact or invite attribution. Server-side registration `source` field is the canonical record; committed `metrics/share_attribution_count.sql`; **field live + verified by a test registration by 2026-11-15, else FAILED**; denominator floor n≥50, else FAILED; denominator restricted to web + Android (install-referrer) unless the iOS deferred-deep-link work item ships — named exclusion, not silent. [verify fixes]
- **(B)** Cumulative installs **≥1,500** on the 2027-01-08 snapshot line.

**Tripwire 2026-11-15 (binary, no fictional remediation):** archived projection script extrapolates trailing-4-week growth; projection <750 cumulative → immediate ADR forcing a binary: sanction the founder-funded paid probe (**$200–500, entity-level, pre-authorized at §9 decision 4**) to measure real CAC — since paid is the category's only proven install engine at volume — or freeze. *(First draft rolled a 4-week "remediation" that its own channel math said also fails.)*

**Kill (full partition):** installs <750 on 2027-01-08 or tripwire-binary freeze → portfolio ADR (strategic sale, if any, executes from frozen state and does not delay the kill). Partial (750–1,499, or share-attribution <10% with installs ≥1,500) → ONE quarter extension to 2027-04-08, identical gate; second miss → freeze ADR.

**Also in this stage:**
- **Live Quiet Room ships here as an experiment** — WITH the Apple-guideline-1.2 moderation baseline (report/block flows, published contact, 18+ enforcement, crisis-resource interstitial) **at first submission**, not deferred to Stage 5. [critic fix — the first draft invited a UGC rejection at the exact submission a gate depended on]. Two daily anchor windows matched to real geography (21:00 IST / 09:00 US-East). Network bar: ≥100 completed matched sessions in the Dec window → repeat-pair moat sanctioned; <25 → degrade to solo by ADR (moat claim reverts to brand+ASO; Stage-5/6 kill thresholds tighten as written).
- **Zero-cost partner probe:** free 90-day code packs (Play promo / Apple offer codes) to ADHD coaches; success = ≥10 coaches × ≥3 redemptions; failure costs nothing.
- **'Year in Gentle' December recap artifact** timed for the share window; Pinterest launch; gentle post-positive-moment review prompt; Apple featuring nomination (lottery ticket, free).
- **Neutral-named entity decision executes** (§9 decision 3) so Stage 3's paywall doesn't publish the family name.

**Unlocks:** monetization go (Stage 3); coach-code lane if probe passed; merchant/GST paperwork checklist drafted for founder execution. ADR-006 completes here; continuation is by new ADR.

---

### Stage 3 — Gentle Freemium, Calibration Point · 2027-01-09 → 2027-05-08

**Objective:** Launch GentleQuest Plus on store IAP (the only rail — cross-border Stripe blocked) via the only grounded willingness-to-pay mechanism in the category, without betraying the no-guilt brand — and treat the result as **the measurement that re-derives all downstream arithmetic**.

**Exit gate (single metric, read frozen 2027-05-08):** **≥250 distinct active paid subscriptions** on the 2027-04-30 ASC + Play subscription reports, per committed `metrics/paid_subs_count` script. *(First draft gated $1,000 trailing-30d proceeds — broken four ways: Apple financial reports can't be summed over arbitrary windows; "net proceeds" was undefined across refunds/FX/GST; the 3-month grandfather grant sat exactly on top of the 3-month measurement window so the entire Stage-2 base was structurally unable to convert inside it; and India-weighted ARPU (~$2.5–3.5/mo net, 77% India base) made the dollar bar mean something different than designed. A subscriber count is settlement-lag-proof and geography-proof.)* Dollar series still piped daily (Sales & Trends + Play earnings; Payments reports as ≥45-day true-up) — it feeds the calibration ADR and the founder-quit ledger, it just isn't the gate.

**Kill (full partition on the subs number):** <60 → paywall off (everyone grandfathered), $1B-abandonment ADR, freeze decision to portfolio. 60–249 → ONE pricing/packaging pivot, 8-week retest closing 2027-07-03, identical metric; second miss → paywall off + abandonment ADR, continue as free organic side project. ≥250 → pass.

**Work:** StoreKit 2 + Play Billing via `in_app_purchase` with server-side receipt validation (full build — zero IAP code exists); paywall = Focusmate precedent, pre-stated for both Stage-2 branches (rooms alive → 3 free matched sessions/week, unlimited at $6.99/mo / $49.99/yr; rooms degraded → comfort pack at identical pricing); solo core loop stays free forever, pledge published in-app and on gentlequest.app; **grandfather capped at 30 days** [fix]; **India regional tier at launch**; **tax-reserve rule live** (35% of collected proceeds reserved before any reinvestment) [critic fix]; **Flask → Cloud Run migration completes HERE** (moved from Stage 4 — hardening belongs before the spike, not during it) [verify fix]; **calibration ADR (blocking):** observed blended ARPU + free→paid conversion + geo mix written before any Stage-4 spend.

**Unlocks:** paid marketing permitted under the §5 governor; entity-level ad accounts (neutral entity, no founder name/face).

---

### Stage 4 — Paid Loop Ignition · 2027-05-09 → 2027-11-08

**Objective:** Replicate the category winner's actual engine — paid TikTok/Meta with faceless creative — funded exclusively by collected proceeds, proving payback on calibrated numbers before scale.

**Entry preconditions:** calibration ADR shows test-scale payback ≤12 months; subscription-source attribution field + ad-platform conversion pixels live and test-verified **before the first dollar of spend**. [verify fix — the first draft's CAC kill was unmeasurable: no script, undefined numerator/denominator, modeled LTV]

**Exit gate (2027-11-08, both required):** trailing-30-day net proceeds **≥$2,500** (≈$30k ARR run-rate) per the committed summation script (Sales & Trends + Play daily earnings basis, net-proceeds definition frozen in code: post-commission, refunds settled as of read-date, ECB FX on window close, GST excluded); AND `payback_months = blended_CAC ÷ calibrated_monthly_ARPU` **<12** at the last two month-closes — frozen formula, store-report subscriber delta as denominator, no re-modeling. *(First draft demanded $25,000 = 25x in 6 months = 71%/mo compounding; the governor's own ceiling is ~8–12%/mo → ~1.6–2x. The gate was unreachable by construction.)*

**Kill:** payback >12mo at 2 consecutive month-closes → governor allowance $0 within 7 days, organic posture resumes (restart only after payback re-proves <12mo × 2 months at test budget). Gate <$1,200 → halt paid, one re-gate 2028-02-08, identical bar; second miss → $1B-abandonment ADR, run profitable at whatever holds.

**Work:** entity-level TikTok/Meta accounts (no founder name/face in any creative or account); AI-fleet creative factory 20+ faceless variants/week recut from organic artifacts + creator content; coach lane scaled if the Stage-2 probe passed (promo-code-only); weekly cohort payback at each month-close; Android parity push (larger ADHD TAM; iOS 155 vs 17 today); top-5-locale listing + paywall localization.

**Unlocks:** **quit trigger ARMED** — MRR ≥2x monthly day-job salary sustained 3 consecutive months → the quit decision goes to the founder, on the founder's terms. **The fork decision (Stage 5 Track F vs B)** goes to the founder with real payback data. Contractor hiring stays deferred until trailing-30d collected ≥$40k.

---

### Stage 5 — Category Leader (forked) · 2027-11-09 → 2030-06-30

**Objective:** Scale the proven loop to make GentleQuest the default ADHD companion — own "body doubling" and "ADHD companion" in store search and short-form culture. *(First draft demanded 33x in 21 months — requiring ~4.3-month payback while its own kill accepted <12 — mutually inconsistent. Fixed by naming the fork instead of pretending.)*

**Entry precondition (capacity, no gate verified it before):** founder is full-time on GentleQuest, OR ≥2 contractors are hired and onboarded. If neither, Track F is unavailable and Track B's dates slip by written ADR. [critic fix]

**THE FORK (by ADR, founder's call, made with Stage-4 payback data in hand):**
- **Track F — funded (default for the $1B endpoint):** raise seed/Series-A ($1.5–3M) on proven payback, through the incorporated entity (§9 decision 3 — investability was never buildable on a non-corporate entity with no IP-assignment chain; that work happens in Stages 2–4). Governor re-capped by ADR with named raise size, burn, and dilution written into the math. **Gate: trailing-30d net proceeds ≥$833k (=$10M ARR run-rate) by 2030-06-30**, per committed script, cash-collected basis (audited bookkeeping is advisory reconciliation with a tolerance band, not the gate). **Midpoint kill 2029-03-31: trailing-30d <$100k → drop to Track B, ADR recorded.**
- **Track B — bootstrap:** governor unchanged. **Gate: trailing-30d ≥$100k (=$1.2M run-rate) by 2030-06-30.** Passing = profitable niche leader on the Finch-class trajectory; the $1B path is formally re-dated only if measured growth sustains >12%/mo, else the exit-optimization posture ($150–300M-class outcome) is adopted by ADR — a success, stated as one.

**Both tracks:** monthly churn ceiling <5% as a rollback-enforced ship-gate (a <12mo-payback/high-churn loop passes every payback check and still can't compound — the governing formula `g = reinvest/payback − churn` is published in the ledger and recomputed monthly); quarterly CAC re-calibration checkpoint (funded incumbents compress auctions faster than a 2-month lagging kill can catch) [critic fix]; Sean-Ellis PMF survey instrumented before entry or struck from all gates; rooms scale only with the safety baseline already shipped in Stage 2; hire 2–4 contractors at ≥$80k/30d collected; strategic-option-in-writing (LOI) maintained as midpoint downside protection.

---

### Stage 6 — $100M Territory · 2030-07-01 → 2033-06-30 *(Track F only)*

**Objective:** Compound ~2.3x/yr for three years from $10M run-rate to $100M+ — the ADHD operating system, not just a companion app — landing at <2% of the projected 2033 category.

**Exit gate (metric-consistent with Stage 5 — the first draft silently switched from run-rate to TTM-recognized-revenue and back, letting the same reality pass one reading and fail another):** **trailing-30-day net cash proceeds ≥$8.33M (=$100M run-rate) by 2033-06-30** per committed `metrics/stage6_revenue` script over ASC + Play financial reports **+ bank-collected B2B2C ledger** (contracted value counts only when invoiced AND collected, bank-reconciled). TTM audited recognized revenue (recognition policy pre-committed by ADR: ratable over term, refunds netted, B2B2C on collection) runs as lagging confirmation — flag, don't fail, at >10% divergence.

**Annual kill checkpoints (same metric, single thresholds — no ARR/revenue metric-switching):** 2031-06-30 trailing-30d <$2.0M → exit-optimization ADR; 2032-06-30 <$4.5M → same. NRR + logo churn pulled monthly; if the self-funded ceiling math shows the required rate is unreachable and no further capital is chosen, the checkpoint ADR fires early rather than discovering it at the gate.

**Work:** companion → ADHD OS (planner/focus/routines, family plans, body-doubling liquidity deepening if the network branch lives); top-20 locale localization + follow-the-sun anchor windows; **B2B2C entered only now, from consumer density** (employer neurodiversity/EAP, university disability offices — with counsel, collections staffed, never medical-device claims); commission math restated at the 30%/15% blend; M&A tuck-ins with equity; growth round or continued compounding.

**Endpoint:** $1B valuation territory via IPO, growth equity, or strategic acquisition — with the credible option to stay independent, since every gate was passed on collected cash and none on borrowed arithmetic.

---

## 7. Kill-grade risk register (synthesis + 18-gap critique, condensed)

| # | Risk | Bites at | Mitigation in-plan |
|---|---|---|---|
| 1 | **Stage 0 fires** — 0/3 criteria, 31 days, fastest lever (ASO) mostly lands after the window | Aug 8 | Human-voice declared primary; creator blitz 80–120 wk 1; instrumentation by Jul 18. Honest odds: this is the modal outcome; the roadmap honors it |
| 2 | Attachment unproven — 7-day actives = 2; D-retention never measured | Stage 1 | D14 gate with n-floor; roadmap deterministically kills itself in Oct on its own honesty if attachment isn't real |
| 3 | Organic channel math ~7–14x under any big install number | Stage 2 | Gate re-based to loop quality; Nov-15 binary tripwire; paid probe pre-authorized |
| 4 | **Trader/seller disclosure breaks pseudonymity at monetization** — store listings publish the legal entity name, which contains the family name | Stage 3 | Neutral-named entity incorporated in Stage 2 (§9 dec. 3) — also what makes Stage 5 investable |
| 5 | Moonlighting exposure window — GST/merchant paper trail while bank-employed; quit trigger can't arm before mid-Stage 4 | Stages 3–4 | Neutral entity + minimal-surface registration; founder-gated timing; no public founder brand at any stage |
| 6 | "$0 burn" was false — payout lag 30–60d + ~30% advance tax | Stages 3–6 | Governor rebuilt: monthly ≤65% of collected; tax reserve at Stage 3 |
| 7 | Apple UGC rejection on rooms (guideline 1.2) | Stage 2 | Moderation baseline ships AT first rooms submission |
| 8 | Single-rail dependence — one store account action = death | All | Web/PWA build kept alive as hedge; store privacy declarations audited Stage 0; policy-watch agent weekly |
| 9 | Crisis/liability at bus-factor 1 — anonymous rooms, vulnerable population | Stage 2+ | Safety baseline at submission; ToS/insurance review before rooms scale (Stage 4/5); counsel before B2B2C |
| 10 | DPDP/GDPR on server-persisted journals + mood data | Stage 2+ | Journal fix + declaration audit Stage 0; privacy program funded from Stage 3 proceeds |
| 11 | Mac SPOF — execution fleet AND gate artifacts on one laptop | All | Off-Mac artifact copies Stage 0; OCI hedge exists |
| 12 | Incumbent copy of the wedge (Finch/Inflow/Tiimo within a release cycle) | Stages 0–2, 5 | Weekly competitor sensor; network layer is the designed counter; if it degrades, moat honestly reverts to brand+ASO and kill thresholds tighten |
| 13 | Founder burnout — workload compounds, relief only at $80k hires | Stages 1–5 | Stage-5 capacity entry precondition; scope cuts (rooms out of S1) already applied; ~2h/wk operator budget re-derived at each stage ADR |
| 14 | Commission-tier lapse at $1M/yr (15% → 30% first-year) | Stages 5–6 | ARPU math already restated at the blend |

## 8. What passing looks like (the honest chain)

39 installs today → *any human voice* (Aug 8) → 250 installs + D14 ≥15% (Oct 8) → share loop ≥10% + 1,500 (Jan 8 '27) → 250 paying subs (May 8 '27) → $2.5k/30d + payback <12mo (Nov 8 '27) → **fork** → $833k/30d funded (mid-2030) → $8.33M/30d (mid-2033) ≈ **$100M ARR ≈ $1B territory**. Seven years, seven gates, every one a formula over a named artifact, every failure a written ADR that stops the clock honestly. Bootstrap fallback at every fork lands at a $150–300M-class profitable niche leader — named as a success, not a consolation.

## 9. Operator-gated decisions (nothing here self-executes)

1. **Adopt this roadmap by ADR** (or amend) — until then it binds nothing beyond already-committed ADR-005/006 work.
2. **ADR-006 Gate-6 amendment** — re-base the 10,000-install figure to the Stage-2 dual gate (loop quality ≥10% + 1,500 cumulative). The old number is 7–14x above grounded channel physics and its own tripwire projected landing inside its own kill band.
3. **Neutral-named entity** (Pvt Ltd/LLP, name free of family name) — must exist before any paywall ships (Stage 3), or the store listing publishes the family name. Also the vehicle that makes Stage 5 investable (IP assignment, cap table). Timing/cost is a founder call; latest safe start ≈ Nov 2026.
4. **Pre-authorize the Stage-2 paid probe** ($200–500, entity-level, faceless) so the Nov-15 tripwire binary can execute without a mid-crisis approval round-trip.
5. **ASO title** ("GentleQuest: ADHD Companion") — deferred by your 2026-07-04 call (no "ADHD" in visible copy this turn); revisit at the next ASO cycle with Stage-0 keyword data.

## 10. Stage 0 — this week (2026-07-08 → 07-14)

All agent-executable except where marked 🔑 (founder keyboard):

1. Commit the three ADR-005 counting scripts to `~/gentlequest/metrics/` (web-install delta / non-direct sum / human-voice ledger validator).
2. Wire feedback widget → backend; verify a test submission lands in the table. **Deadline Jul 18, blocks everything downstream.**
3. UTM-tag all live content surfaces; repoint topics to the wedge.
4. Draft 80–120 creator-barter emails (AI fleet) → 🔑 founder sends in one bundled session this week.
5. Journal privacy fix scoped + shipped in a v1.5.1 metadata/patch cycle; 🔑 store privacy-declaration audit (Play Data Safety + Apple labels).
6. Daily off-Mac copy of `funnel_snapshot.log` + `analytics_latest.json`.
7. Stand up the weekly competitor-sensor script.

---
*Full evidence chain: workflow run `wf_239a65a2-51d` (28 agents, 2.2M tokens) — journal at the session transcript dir. Grounding facts, three candidate roadmaps, judge scorecards, 12 adversarial verdicts, and the 18-gap critique are all preserved there verbatim.*

---
## Provenance note — committed 2026-08-27
This document is cited as the canonical gate source by docs/gates/ADR-005, ADR-006 and ADR-007, and its adoption is recorded 2026-07-10. Until today it existed only as a gitignored working-tree file (.gitignore ignores docs/strategy/), tracked nowhere and backed up by nothing — one `git clean` from loss. Committed (git add -f, path unchanged, DRAFT header preserved) to end that state. Committing records it; it does not re-litigate its contents or its adoption status.
