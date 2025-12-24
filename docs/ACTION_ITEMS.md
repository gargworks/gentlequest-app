# GentleQuest Action Items & Implementation Plan
## Last Updated: Dec 22, 2025

---

## 🚀 IMMEDIATE TASKS (This Week)

### 1. In-App Feedback Prompt Implementation
- **Status**: Ready to start
- **Trigger**: After 3rd check-in completion
- **Implementation**: 
  - Add counter in SharedPreferences for check-in count
  - Show feedback dialog when count == 3
  - Simple rating + optional text feedback
  - Store feedback in backend /analytics endpoint

---

## 📋 SEQUENCED PLAN (Updated Priorities)

### Week 2 (Dec 29-Jan 5)
1. **In-app feedback prompt** - Implement after 3rd check-in
2. Monitor beta feedback from friends/family
3. Review/optimize existing haptic patterns

### Week 3 (Jan 6-12)
1. Monitor retention metrics
2. Collect feedback from current users
3. Plan next iterations based on feedback

### Month 2 (February 2026)
1. **PHQ-9/GAD-7 Clinical Assessments** (see details below)
2. Clinical advisor outreach (using existing XLSX contacts)
3. User interviews (target: current user base first)

### Month 3 (March 2026)
1. B2B pitch deck creation
2. University/company pilot outreach
3. Outcome measurement dashboard

---

## 🎯 DETAILED TASK BREAKDOWNS

### PHQ-9/GAD-7 Implementation Plan
**What we need:**
1. Assessment UI screens (multiple choice questions)
2. Score calculation and storage
3. Progress tracking over time
4. Clinical resources based on scores

**Implementation approach:**
- Add new tab: "Assessments" 
- Weekly/bi-weekly prompts (not daily)
- Store scores with timestamps
- Show trend graphs to users
- Export capability for therapists

**Files to create/modify:**
- `lib/screens/assessment_screen.dart` - Main assessment UI
- `lib/widgets/phq9_widget.dart` - PHQ-9 questions
- `lib/widgets/gad7_widget.dart` - GAD-7 questions
- `lib/providers/assessment_provider.dart` - State management
- Backend: Add `/api/assessment` endpoints

### Clinical Advisor Outreach
**Contact list location**: 
- Please place the XLSX file at: `/docs/contacts/psychologists_india.xlsx`
- I'll read it and help prepare outreach emails

**Outreach strategy:**
- Focus on Indian psychologists first
- Offer free access in exchange for feedback
- Target: 2-3 advisors for initial validation

### Target Audience Clarification
**Current focus remains:**
- General users (no specific age targeting yet)
- Students experiencing stress/anxiety
- People on therapy waitlists

**Note**: Will NOT change prompts to "young professionals" yet. Keeping scope broad until we have data.

### Case Study Documentation Requirements
**Data points to collect:**
- User testimonials (with permission)
- Before/after mood scores
- Usage patterns and engagement
- Specific outcomes achieved

**Implementation when ready:**
- Add consent form for case studies
- Export feature for user data
- Template for presenting results

### Error Message Status Check
**Need to verify**: Current error messages in the app
- Will check all error states
- Determine if warm tone updates are needed

### Welcome Back Messages Status
**Need to verify**: Existing greeting logic
- Check if contextual messages already exist
- Assess if enhancements are needed

---

## ✅ COMPLETED ITEMS
- Phase 1 emotional design
- Haptic feedback everywhere
- Confetti celebrations
- Retention tracking
- Beta messages sent
- Documentation updated

---

## 📂 File Locations for Reference

### For XLSX Contact List
```
/Users/lokeshgarg/ai-mvp-backend/docs/contacts/psychologists_india.xlsx
```

### Assessment Screens (to be created)
```
ai_buddy_web/lib/screens/assessment_screen.dart
ai_buddy_web/lib/widgets/phq9_widget.dart
ai_buddy_web/lib/widgets/gad7_widget.dart
ai_buddy_web/lib/providers/assessment_provider.dart
```

---

## ⚠️ DEFERRED ITEMS
- Render free tier upgrade (handle in Jan)
- Database migration (handle before expiry)
- Managed Redis setup (evaluate later)
- Error message rewriting (verify current state first)
- Welcome back contextual messages (verify current state first)
- XP popup animations (low priority)
- Mood trend mini-graph (low priority)

---

*This plan is locked until next review on Jan 12, 2026*
