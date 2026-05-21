# LinkedIn Two-Pronged Strategy — Eidetic Works / Axis Career

**Status:** Prong A traction-gated (activate after X/Reddit signal lands; deferred at Day 12 prioritization). Prong B active now, low-cadence.
**Owner:** Lokesh (personal prong) + Distribution Officer (company prong, Telegram-approved).
**Canonical refs:** ADR-018 (brand = Eidetic Works LOCKED), PLAN.md:433/464.
**Last updated:** 2026-05-21
**ADR pointer:** ADR-022 — "LinkedIn two-prong strategy + admin-identity behavioral firewall."

## 1. Executive Summary

Two LinkedIn presences that must NEVER publicly connect:

- **Prong A — `Eidetic Works` company page.** Pseudonymous product brand. Build-in-public numbers, no founder identity.
- **Prong B — Lokesh Garg personal profile.** Axis-facing. Builds Head-of-AI / SVP-Analytics-and-AI credibility via AI-practitioner depth. **Never names Eidetic Works, Nucleus, or the daemon.**

**THE KILL RULE (HARD, existential):** The two prongs do not cross. No cross-follow, no shared admin identity surfacing, no shared email, no product names on the personal profile, no Lokesh identity on the company page. Rationale: moonlighting exposure threatens a ₹70L Axis VP role + the FY26 appraisal / CEO-track path. Pseudonymity buys time, not permanent cover — so the firewall is **behavioral discipline**, not a one-time setup.

Source: PLAN.md:433 ("Nothing on Lokesh's LinkedIn references Nucleus or Eidetic Works. Axis VP role stays clean."), PLAN.md:464 (HARD KILL: "Personal LinkedIn brand around Nucleus | Kill | Moonlighting risk is binding").

## 2. Prong A — Eidetic Works company page

### Admin identity — RESOLVED: real-Lokesh-account + behavioral firewall

**The decision:** Lokesh's real LinkedIn personal account admins the Eidetic Works company page. **Burner / duplicate accounts are REJECTED.**

**Why not a burner:**
- LinkedIn TOS §8.2 prohibits duplicate/secondary personal accounts. Detection via IP, device fingerprint, behavioral correlation, and Buffer's OAuth call pattern is reliable.
- Failure mode if detected: BOTH the burner personal account AND the Eidetic Works company page deleted, no appeal. That nukes the career-critical surface (the real account) AND the brand surface simultaneously — worst possible outcome.
- LinkedIn does **not** publicly display company-page admins on the public-facing page. The realistic moonlighting threat (Axis colleague stumbles onto the page, recognizes Lokesh) is already addressed by this default.

**The pseudonymity work is done by behavioral discipline, not by hiding the admin link in LinkedIn's internal DB:**
- ❌ NEVER add Eidetic Works to your personal Experience section. Decline every "add this company to your profile" prompt LinkedIn shows during page setup.
- ❌ NEVER like, comment, reshare, or interact with the Eidetic Works page from your personal profile. Any interaction creates a public graph edge.
- ❌ NEVER follow the Eidetic Works page from your personal account.
- ❌ NEVER list yourself as a publicly-surfaced "Page Member" or "Team Member" — Admin role only.
- ✅ DO: turn off Activity Broadcasts on your personal profile (Settings & Privacy → Visibility → Activity broadcasts → OFF) so admin actions don't leak to your connections feed.
- ✅ DO: do all Eidetic Works admin work in a separate Chrome profile, isolated from work-laptop sync if any.
- ✅ DO: Buffer's `BUFFER_PROFILE_LINKEDIN` secret must point to the **company** profile ID — never the personal profile ID. Catastrophic misconfig: personal feed starts auto-posting Eidetic content.

**Cleanest hedge:** Defer the company page entirely until the traction-gate clears (per Day-12 prioritization — first paid Pro signal from X). If the page doesn't exist, the admin problem is moot.

### When activated (post traction-gate)

- **Cadence:** 1 post/day via Buffer once activated (DISTRIBUTION_AUTOPILOT.md:31). Until traction-gate clears, 0/day.
- **Voice:** Distribution Officer charter — numbers-led, direct, no hype. Exemplar: `work/docs/posts/linkedin-day12.md`.
- **Content sources:** SHIPPED.md shipped-work + daemon metrics (P95, engram counts) + unit-economics actuals.
- **Approval:** Telegram per Distribution Officer charter. Never auto-post raw drafts.
- **Hashtags:** sparse — `#AI` `#LocalFirst` `#DevTools` max 3, no `#buildinpublic` spam.
- **Engagement rules:** company-page replies stay product-substantive; never reply in a way that reveals operator location / employer / identity.

## 3. Prong B — Personal profile (Axis career hedge)

- **Cadence:** 1-2x/week. This is a *credibility hedge*, not a campaign — sustainable beats frequent. Tues/Thurs 8-9am IST (banker-network active hours).
- **Voice:** senior practitioner. "Deep practitioner understanding of AI — hands-on, not theoretical" (`.brain/thrive_april2026.md:760`). Measured, credible, zero indie-bro.
- **Content slots (the green zone — claim as expertise without naming the product):**
  - AI architecture patterns (orchestration, multi-agent coordination — generic)
  - Memory / context-management abstractions in LLM systems
  - AI-in-BFSI observations (governance, productivity, risk — your actual day-job lens, draws from your Axis BIU work)
  - Reactions to Anthropic / OpenAI / industry developments with a practitioner take
- **Tone guardrails:** "too professional" reads as a manager who doesn't build → fail. "Indie-bro" reads as moonlighter → fail + leak risk. Land at: *the rare senior banking exec who actually understands the architecture.*

## 4. Separation Rules

**KILL LIST (never on personal profile, never linkable):**
- "Eidetic Works," "Nucleus," "NucleusOS," daemon, eidetic-daemon
- Revenue, MRR, paid-user counts, waitlist numbers
- Product screenshots / UI / any visual identifying the product
- "I built / I'm building / my startup / founder"
- Any link, even oblique, between Lokesh and the company page (cross-follow, like, comment, mutual mention)

**GREEN LIST (safe to claim as personal expertise):**
- AI orchestration / agent-coordination patterns (generic, no product)
- Memory systems & context-window management as *concepts*
- MCP / tool-use architecture discussed abstractly
- AI productivity in regulated / banking environments
- Cost optimization of LLM workloads (the cost-playbook *thinking*, never the product)

**AMBIGUOUS — worked examples:**
- ✅ "Spent the weekend benchmarking local-first memory retrieval for LLM agents. Sub-millisecond P95 is achievable with the right indexing." → generic technique, no product, defensible as personal research.
- ❌ "Our daemon hits 0.27ms P95 on 141K engrams." → "our" + specific product metrics = direct leak.
- ✅ "Most AI memory tools are cloud-bound. The interesting design space is local-first + vendor-neutral." → opinion / architecture, claimable.
- ❌ "Check out what I'm building at eidetic.works" → catastrophic, kill-list violation.
- ⚠ Speaking at a banker AI conference: fine — present AI-orchestration *patterns* as a practitioner. Do NOT demo the product or use a bio that names Eidetic Works.

## 5. Axis Thrive Integration

Personal-prong content feeds the FY26 Thrive SVP-positioning narrative (manager: Amit Mohole, per `memory/user_employment_context.md:7-15`). Mechanism: each personal post demonstrating AI-practitioner depth is evidence for the "deep hands-on AI understanding" band-positioning. Monthly: refresh the personal narrative with *abstracted* learnings from Eidetic work (techniques, patterns — never the product). The product is the lab where the judgment was earned; the personal profile shows the judgment, not the lab.

## 6. Monitoring & Exceptions

**Leak-detection signals (any → escalate):**
- An Axis colleague likes / comments on the Eidetic Works page
- A journalist or competitor publicly connects Lokesh ↔ Eidetic Works
- Commit-email forensics or codebase-similarity surfaces the link
- LinkedIn "people also viewed" or mutual-connection graph starts bridging the two profiles
- Any third-party service (Buffer, X, Slack, GitHub) sends a notification to an Axis-monitored inbox referencing Eidetic Works

**Escalation flow if breached:** (1) stop all personal-prong AI-adjacent posting immediately; (2) assess scope — casual observer vs Axis-compliance-level; (3) if Axis-compliance-level, the Day-30 disclosure plan (ADR-007) compresses to "now" + consult the moonlighting-policy position; (4) log to DECISIONS.md as an extraordinary ADR.

**30-day refresh:** re-read this doc + re-run leak-detection scan monthly. Renew or revise.

## Day-1 Action Checklist

**Personal prong (this week, ~30 min):**
- [ ] One green-zone post (architecture / memory-systems take, no product). Use the `linkedin-post-2026-05-18.md` voice exemplar.
- [ ] Confirm the personal profile has zero Eidetic Works / Nucleus references anywhere (headline, about, activity).
- [ ] Settings & Privacy → Visibility → Activity broadcasts → OFF.
- [ ] Settings & Privacy → Profile viewing options → set to private mode while doing company-page admin work (revert to normal after).

**Company prong (ONLY if traction-gate cleared):**
- [ ] Set up a separate Chrome profile dedicated to Eidetic Works admin work.
- [ ] Create Eidetic Works company page from real Lokesh LinkedIn account.
  - During setup: DECLINE every "Add this company to your profile" prompt.
  - In page Settings → Admins: confirm only `Admin` role on Lokesh, NOT "Page Member" / "Content Admin" / "Curator" (these are publicly listed).
- [ ] Connect Buffer's LinkedIn channel to the COMPANY page (not personal). Verify in Buffer settings.
- [ ] First post = the ready daemon-launch draft (`work/docs/posts/linkedin-day12.md`).
- [ ] Run the leak-detection scan (see §6) after first post — confirm no graph edges accidentally formed.

**Banker-network targeting (Day-61+ career-hedge activity — framework only):**
Target role-titles to source via verified LinkedIn search (operator-assistant runs lookups; verify each before any outreach): Head of AI / Head of Analytics / Chief Data Officer at HDFC, ICICI, Kotak, SBI, Yes Bank, IndusInd, IDFC First, Federal, RBL, AU Small Finance. Engagement = thoughtful comments on their posts first (3-4 weeks of presence) before any connection request. **Do not fabricate this list — source real current URLs, verify role tenure, then engage.**
