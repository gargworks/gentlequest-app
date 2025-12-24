# GentleQuest Hero Flow Documentation

**Date:** December 21, 2025  
**Purpose:** Document the core user journey that drives retention

---

## Hero Flow Definition

The hero flow is the primary repeatable journey that delivers value to users and drives daily engagement:

```
Quick Check-in (2 min) → Optional AI Chat → Quest Completion → XP Reward → Mood Analytics
```

---

## Flow Breakdown

### 1. Quick Check-in (Entry Point)
- **Location:** Wellness Dashboard (prominent "Start" button)
- **Duration:** ~2 minutes
- **Components:**
  - Mood selection (5-point scale: Sad, Anxious, Neutral, Calm, Happy)
  - Energy level (Very Low → Very High)
  - Sleep quality (Poor → Excellent)
  - Stress level (Very Low → Very High)
  - Optional notes
- **Gating:** Once per day via `daily_quick_checkin_completed_YYYY-MM-DD_utc` flag
- **Outcome:** Data captured for personalization

### 2. Optional AI Chat (Support)
- **Trigger:** After check-in completion or direct navigation to Talk tab
- **Persona:** Supportive AI assistant (currently "high school students" persona)
- **Safety:** Crisis detection with geo-specific resources
- **Provider Fallback:** Gemini → OpenAI → Perplexity
- **Outcome:** Emotional support and coping strategies

### 3. Quest Completion (Reinforcement)
- **Trigger:** Automatic after check-in submission
- **Quest ID:** Dynamically fetched from today's items (tag: CHECK-IN)
- **Action:** `engine.markComplete(questId)`
- **Reward:** XP (QuestsEngine.xpOther = 10 XP)
- **Visual Feedback:** Ripple animation + XP pop notification
- **Outcome:** Progress tracking and achievement

### 4. XP & Progress (Gamification)
- **Systems:**
  - Daily XP from check-ins
  - Lifetime XP tracking
  - Badge progression (based on streak days)
  - Weekly Pulse (after 3+ mood entries)
- **Sync:** ProgressProvider updates after quest completion
- **Outcome:** Long-term engagement hooks

### 5. Mood Analytics (Reflection)
- **Location:** Mood tab
- **Features:**
  - Mood history visualization
  - Streak tracking
  - Weekly insights (trend analysis)
  - "You Are Not Alone" messages
- **Outcome:** Self-awareness and pattern recognition

---

## Current Performance

- **Total Time:** ~2-3 minutes for complete flow
- **Friction Points:** 
  - AI persona mismatch for professional users (noted for future)
  - No push notification reminders (planned for retention)
- **Completion Rate:** To be measured with beta testing

---

## Optimization Opportunities

1. **Reduce Friction:**
   - Pre-fill yesterday's values as defaults
   - Add keyboard shortcuts for rapid input
   - Minimize animation delays

2. **Increase Personalization:**
   - Connect mood to quest suggestions
   - Tailor AI responses based on stress/energy levels
   - Show relevant insights immediately after check-in

3. **Retention Hooks:**
   - Day 2/3 push notifications
   - Streak recovery mechanisms
   - Social sharing after 3rd check-in

---

## Success Metrics

- **Primary:** 7-day retention (completed check-ins)
- **Secondary:** 
  - Time to complete hero flow
  - AI chat engagement rate
  - Mood analytics view frequency
  - Streak length distribution

---

## Status

- [x] Hero flow identified and documented
- [x] Base implementation functional
- [ ] North star metric chosen (7-day retention)
- [ ] Retention tracking implemented
- [ ] Push notification system added
- [ ] Personalization features shipped
