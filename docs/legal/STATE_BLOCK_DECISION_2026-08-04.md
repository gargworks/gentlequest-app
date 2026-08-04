# State Block Decision Record — 2026-08-04

**Status:** DECISION PENDING (founder approval required)
**Author:** Devin (AI agent) + legal research subagents
**Trigger:** 24.1% block rate (35/145 users) identified as top acquisition funnel friction

---

## 1. SITUATION

GentleQuest blocks users in 3 US states (IL, UT, WA) via:
- `compliance_service.dart` — `_hardBanStates` (IL) + `_pendingComplianceStates` (UT, WA)
- `routes/compliance.py` — `HARD_BAN = {"Illinois"}` + `PENDING = {"Utah", "Washington"}`

**Block rate data (Firebase analytics, Feb–Mar 2026):**
- 145 compliance checks started
- 35 users blocked = **24.1% block rate**
- Alert threshold in `analytics_dashboard.py` is >20% — currently triggered

**Population impact:**
- IL: 12.6M (3.8% of US)
- UT: 3.4M (1.0% of US)
- WA: 7.9M (2.4% of US)
- Total blocked: 23.9M (7.1% of US population)

---

## 2. LEGAL RESEARCH FINDINGS

### Illinois — HB 1806 (WOPR Act), effective Aug 1, 2025
- **Penalty:** $10,000 per violation
- **What it bans:** AI making therapeutic decisions, holding therapy conversations, drafting treatment plans, analyzing emotions for therapeutic purposes
- **Exemption:** "Self-help apps sold as nothing more as self-help"
- **GQ status:** Terms say "wellness companion, not a medical device, therapy service." Leopard system prompt says "NO Therapy Speak." Safety sheet says "AI-based wellness support. It does not provide medical advice, diagnosis, or treatment."
- **Likelihood GQ is exempt:** HIGH

### Utah — HB 452 (Mental Health Chatbots), effective May 7, 2025
- **Penalty:** $2,500 per violation (administrative)
- **What it covers:** "Mental health chatbots" that simulate licensed therapist conversations
- **Exemption:** Scripted outputs, tools that connect to human therapists, self-help apps
- **GQ status:** Alex is positioned as wellness companion, not therapy. No claims of therapeutic benefit. Crisis detection routes to 988 (human escalation).
- **Likelihood GQ is exempt:** HIGH

### Washington — HB 2225 (AI Companion Chatbot Law)
- **Penalty:** Private right of action (uncapped damages)
- **Effective date:** **January 1, 2027** — NOT YET IN EFFECT
- **What it covers:** AI chatbots that sustain relationships, ask unprompted personal questions, retain preferences
- **Exemption:** On-demand tools that don't sustain relationships
- **GQ status:** Chat is user-initiated, on-demand. Alex doesn't proactively message users or ask unprompted questions.
- **Likelihood GQ is exempt:** HIGH
- **Current risk:** ZERO (law not in effect until 2027)

### Colorado — SB 26-189 (AI Act), effective Jan 1, 2027
- **Status:** Already ALLOWED in GQ (not blocked)
- **Why:** Law covers "consequential decisions" in 7 domains (employment, housing, lending, etc.). Mood tracking + blog content explicitly excluded. Content generation is carved out.
- **No action needed.**

---

## 3. EXISTING COMPLIANCE SAFEGUARDS (Already Shipped)

GQ already has these disclosures and safety features — no new build required:

| Safeguard | Location | Content |
|-----------|----------|---------|
| Persistent chat footer | `interactive_chat_screen.dart` L909-925 | "Not medical care. For crisis, call local emergency." |
| Safety/Legal sheet | `safety_legal_sheet.dart` | "AI-based wellness support. It does not provide medical advice, diagnosis, or treatment." |
| Terms of Service | `assets/legal/terms.md` §2 | "GentleQuest is a wellness companion, not a medical device, therapy service, diagnosis tool, or treatment." |
| Crisis detection | `chat_helpers.py` + `crisis_keyword_detector.dart` | On-device keyword detection → 988 routing |
| AI system prompt | `leopard_system_prompt.dart` | "NO Therapy Speak. FOCUS on Action, Agency, and control." |
| Age gate | `compliance_service.dart` | Universal 18+ |
| Privacy policy | `docs/legal/privacy_policy.md` | Discloses AI use, crisis data handling, no targeted ads based on mood data |

---

## 4. SCENARIO SIMULATION

| Scenario | Users Recovered | Legal Risk | Implementation |
|----------|-----------------|------------|----------------|
| **A: Keep all blocks** | 0 (24.1% lost) | Zero | None |
| **B: Unblock UT+WA, keep IL** | ~23 (16%) | Very low — WA not in effect until 2027; UT likely exempt | Remove 2 states from block lists |
| **C: Unblock all 3** | ~35 (24.1%) | Low-medium — IL self-help exemption likely applies | Remove 3 states from block lists |
| **D: Unblock all 3 + AI disclosure** | ~35 (24.1%) | Lowest — all disclosures in place | Remove 3 states + add 1-line AI disclosure to chat |

---

## 5. RECOMMENDED PATH: Scenario D

**Rationale:**
1. All 3 laws either exempt self-help/wellness apps or aren't in effect yet
2. GQ already has the disclosures each law requires (AI disclosure, wellness positioning, crisis routing)
3. 24.1% block rate is the single biggest acquisition funnel leak
4. The disclosures are already shipped — no app update needed for the legal positioning
5. If legal counsel later says a state is risky, we can re-block in one line change

**What Scenario D requires:**
1. Remove IL from `_hardBanStates` in `compliance_service.dart`
2. Remove UT, WA from `_pendingComplianceStates` in `compliance_service.dart`
3. Remove `HARD_BAN` and `PENDING` sets from `routes/compliance.py` (set both to empty)
4. Update compliance_service.dart comments to reference this decision record
5. (Optional) Add "Alex is an AI companion, not a human" to the chat footer

---

## 6. FALLBACK PLAN (If Shit Happens)

If any state regulator contacts us or we receive a legal complaint:

### Immediate fallback (can execute in <5 minutes):
1. Re-add the state to `_hardBanStates` or `_pendingComplianceStates` in `compliance_service.dart`
2. Re-add the state to `HARD_BAN` or `PENDING` in `routes/compliance.py`
3. Ship a hotfix app update
4. Document the incident in this file

### State-specific fallback triggers:
- **IL**: If IDFPR contacts us → re-block IL immediately, consult counsel
- **UT**: If Utah AG contacts us → re-block UT, add explicit "not therapy" disclaimer to first chat message
- **WA**: If lawsuit filed → re-block WA, add 3-hour recurring AI disclosure (per HB 2225)
- **Any state**: If we learn of a new state law → add to block list, update this document

### Legal counsel engagement triggers:
- Any regulator contact (IDFPR, state AG, FTC)
- Any user lawsuit or legal threat
- Any new state AI mental health law introduced in legislature
- Annual review (July 1 + Jan 1 per `.github/workflows/compliance_review.yml`)

---

## 7. EVIDENCE TRAIL

### Code references:
- Block lists: `ai_buddy_web/lib/services/compliance_service.dart` L116-142
- Backend: `ai-mvp-backend/routes/compliance.py` L69-71
- Block rate alert: `scripts/analytics_dashboard.py` L307-318
- Existing disclosures: `safety_legal_sheet.dart`, `interactive_chat_screen.dart` L909-925
- Terms: `ai_buddy_web/assets/legal/terms.md` §2
- Privacy policy: `docs/legal/privacy_policy.md`
- Compliance matrix: `docs/v1.4.0/COMPLIANCE_MATRIX.md`
- Legal review brief: `docs/release/LEGAL_REVIEW_BRIEF.md`

### Data sources:
- Firebase analytics: `compliance_check_started` (145), `compliance_blocked` (35)
- Funnel API: `https://app.gentlequest.app/api/metrics/funnel`
- Analytics report: `ai-mvp-backend/metrics/analytics_report.md`

### Legal research:
- Colorado SB 24-205 → SB 26-189 (amended May 14, 2026, effective Jan 1, 2027)
- Illinois HB 1806 (WOPR Act, effective Aug 1, 2025)
- Utah HB 452 (effective May 7, 2025)
- Washington HB 2225 (signed Mar 24, 2026, effective Jan 1, 2027)

---

## 8. DECISION LOG

| Date | Decision | By | Notes |
|------|----------|----|-------|
| 2026-08-04 | Documented analysis + Scenario D recommended | Devin (AI) | Awaiting founder approval |
| | | | |
| | | | |

---

*This document is a decision record, not legal advice. Final state block decisions require founder approval. Consult licensed counsel for formal legal opinions.*
