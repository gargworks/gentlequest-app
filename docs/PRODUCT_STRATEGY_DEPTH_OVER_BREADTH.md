# GentleQuest - Product Strategy: Depth Over Breadth

**Date:** December 21, 2025  
**Context:** Strategic guidance on meaningful product progression

---

## Core Principle

The most meaningful progress on this tool is to stop adding features "horizontally" and instead deepen the **loop** it already has: check-in → personalized support → action → reflection → measurable improvement.

The product already has multiple pillars (interactive chat, quests/XP, mood tracking, wellness dashboard, community, and multiple AI providers), so the biggest wins now come from tightening cohesion, outcomes, and safety across those pillars.

---

## 1. Tighten the Core Loop

Make one primary journey feel inevitable and repeatable (daily/weekly), with everything else supporting it.

### ✅ COMPLETED FEATURES

### Core Loop & Retention
- [x] Quick check-in → AI chat → Quest completion → XP reward
- [x] Daily check-in flag tracking via SharedPreferences
- [x] Retention analytics events (daily_checkin_completed, quest_complete)
- [x] Active days counter (shows Monday-Sunday mood entries)

### Emotional Design Phase 1
- [x] Warm chat greetings (5 variations in gemini.py)
- [x] Celebration snackbars after quest completion
- [x] Active days tracker with gentle progress
- [x] Loading states with encouraging messages

### Crisis Detection
- [x] 11-country geography-specific crisis resources
- [x] IP-based geolocation with fallback
- [x] Crisis resources widget in chat

## 🚧 IN PROGRESS

### Beta Testing
- [ ] Collect feedback from friends/family (WhatsApp)
- [ ] Monitor 7-day retention metrics

## 📋 NEXT 30 DAYS PLAN

### Week 2 (Dec 29-Jan 5)
1. **Haptic feedback** on key actions (VIBE_POLISH_PROMPT.md)
2. **In-app feedback prompt** after 3rd check-in
3. **Phase 2 celebrations** - Confetti for milestones

### Week 3 (Jan 6-12)
1. Send MBA alumni group message
2. Monitor retention metrics
3. Iterate based on feedback

### Month 2 (Feb)
1. Add PHQ-9/GAD-7 clinical assessments
2. Reach out to 2-3 clinical advisors
3. Document outcome improvements

### Month 3 (Mar)
1. Create B2B pitch deck
2. Approach 3 universities/companies
3. Build outcome dashboard for pilots

---

## 2. Outcomes Over Features

To meaningfully progress, define what "better" means and instrument it, then iterate toward that.

### Actions
- Choose 1–2 measurable outcomes (e.g., 7-day retention, "completed 3 check-ins/week," self-rated mood change) and design the product around moving those numbers.
- Turn quests/XP into behavior shaping: rewards tied to clinically sensible habits (sleep routine, journaling, breath exercise), not generic engagement.

### Why it matters
Features don't prove value—outcomes do. Investors, users, and clinicians all ask: "Does this actually help?"

---

## 3. Safety and Trust Layer

For mental-health tools, safety work is product work, not compliance overhead, and it often unlocks distribution and partnerships later.

### Actions
- Add a clear crisis flow (self-harm language detection → encourage professional help → local resources → optional "contact trusted person"), and ensure the assistant never pretends to diagnose.
- Standardize disclaimers, boundaries, and escalation rules across chat, community, and content surfaces so nothing contradicts.

### Why it matters
One safety failure destroys trust permanently. Strong safety = therapist referrals + institutional partnerships + investor confidence.

---

## 4. Make AI Reliable, Not Just Smart

If you support multiple AI providers/models, the meaningful progression is a consistent experience with predictable behavior.

### Actions
- Implement a "response contract" (tone, length, safety checks, citations/grounding rules, refusal behavior) that all providers must satisfy.
- Add lightweight evals: log user intent + model output + user rating, then run weekly regression checks so updates don't quietly degrade quality.

### Why it matters
Smart but unpredictable AI = user distrust. Reliable AI = habit formation.

---

## Next Steps Framework

If you share your current top goal (retention, reviews, paid conversion, or clinical credibility), the next step can be narrowed to the single highest-leverage change to ship this week.

### Decision matrix
| Goal | Highest-leverage change |
|------|------------------------|
| **7-day retention** | Tighten hero flow to <2 min + push notification on day 2/3 |
| **Reviews/social proof** | Add "share your progress" + in-app prompt after 3rd check-in |
| **Paid conversion** | Add value-gate after 7 free check-ins with clear "why upgrade" |
| **Clinical credibility** | Ship crisis flow + get 2 psychiatrists to review safety protocol |

---

## References

This strategy draws from:
- Mental health AI assistant best practices (response contracts, safety layers)
- Product-led growth patterns (hero flow, measurable outcomes)
- Clinical software design (standardized disclaimers, escalation rules)

---

## Status
- [ ] Hero flow identified and documented
- [ ] North star metric chosen (retention / mood / completion)
- [ ] Crisis flow designed
- [ ] AI response contract defined
- [ ] Weekly eval pipeline set up
