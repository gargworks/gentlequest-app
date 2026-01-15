# GentleQuest Crisis Escalation Protocol (B2B Safety Layer)

**Date:** January 9, 2026
**Status:** DRAFT (For Clinical Advisor Review)
**Purpose:** To satisfy University Liability/Safety requirements for B2B pilots.

---

## 1. The "Safety Layer" Philosophy
Unlike Woebot (which explicitly "does not provide crisis intervention"), GentleQuest **embraces** the safety role as a feature.
*   **Competitor Stance:** "We are just a tool; call 911 if hurt."
*   **GentleQuest Stance:** "We are the first line of defense that *successfully hands off* to the University."

## 2. Detection Mechanism: The "Passive C-SSRS"
We do not ask C-SSRS questions every day (too clinical/annoying). We use **Passive NLP Trigger Monitoring**.
If a user's journal entry or chat matches a `Harm_Self` confidence score > 0.85:

**Step 1: The Interrupt**
- **UI:** Screen blurs.
- **Bot:** "I'm detecting that things are really heavy right now, and I want to keep you safe. Can I ask you a direct question?"

**Step 2: The Screener (C-SSRS Short Form)**
1.  "Have you wished you were dead or wished you could go to sleep and not wake up?"
2.  "Have you had any actual thoughts of killing yourself?"

**Step 3: The Triage (Risk Logic)**
- **Low Risk:** (Ideation, no plan) -> "I'm hearing a lot of pain. I'm going to pin the support number here, but let's talk about what's hurting."
- **High Risk:** (Intent/Plan) -> **RED ALERT Handshakes** (See Section 3).

---

## 3. The "Warm Handshake" (B2B Premium Feature)
This is the core value prop for University Counseling Directors.

**Standard App (D2C):**
- Shows "Call 988" button.
- User clicks or closes app. (High drop-off).

**GentleQuest "Campus Connect" (B2B):**
1.  **Direct Patching:** "I can connect you to the [University Name] On-Call Counselor right now. Would you like me to dial?"
2.  **Context Passing (Opt-in):** "Can I share the last 3 messages with them so you don't have to repeat yourself?"
3.  **GPS/Campus Police Integration:** (Only for imminent threat, if University liability requires it).

---

## 4. Liability & Indemnification Strategy
*   **Indemnification:** We indemnify the University for *our tech failing*, but we do not accept liability for *clinical outcomes*.
*   **Disclaimer:** "GentleQuest is an automated support system, not a clinical provider." 
*   However, our **Escalation Log** creates a paper trail proving the University "did everything possible" to provide resources, which shields *them* from negligence claims.

## 5. Implementation Requirements
*   **Tech:** Reliability of the `Harm_Self` classifier must be >99% recall (it catches everything, even if false positives occur).
*   **Ops:** 24/7 uptime monitoring. If the "Escalation Service" goes down, the entire app must go into "Maintenance Mode" to avoid liability holes.

---
*Research Source: Columbia Protocol (C-SSRS), Industry Best Practices for Digital Health.*
