# University Onboarding Workflow - Complete
## From Contract Signature to Pilot Launch (Week 1-3)

## Pre-Onboarding (Contract Signed)

**Immediate Actions (Day 1):**
- Send welcome email (thank you, next steps, timeline)
- Create university record in CRM (HubSpot)
- Assign university ID (for database, alerts, reporting)
- Schedule kickoff call (1 hour, within 7 days)

**Preparation (Day 2-7):**
- Gather university info (CAPS staff, waitlist size, crisis protocol)
- Prepare kickoff materials (agenda, student invitation template, crisis contact form)
- Configure university-specific settings (branding, crisis resources, counselor contacts)

## Week 1: Kickoff & Setup

### Kickoff Call (60 minutes)

**Agenda:**
1. **Introductions (5 min)**
   - Founder, CAPS director, IT (if present)
   - Roles, responsibilities, communication plan

2. **Expectations Alignment (15 min)**
   - Engagement targets: 40%+ weekly active
   - Outcome targets: 20%+ symptom reduction
   - Timeline: 12 weeks pilot, weekly reports, mid-pilot check-in Week 6
   - Success criteria: What does "success" look like for you?

3. **Logistics (20 min)**
   - Student invitation process (who, when, how)
   - Crisis protocol walkthrough (keyword detection → CAPS alert → counselor response)
   - CAPS contact confirmation (email, phone, backup contact)
   - Reporting cadence (weekly Friday 5pm, format, delivery method)

4. **Technical Setup (10 min)**
   - Demo platform access (show features, navigation)
   - Test crisis alert delivery (send test alert, verify received)
   - IT questions (security, integration, support)

5. **Q&A (10 min)**
   - Address concerns (safety, privacy, engagement)
   - Clarify next steps (student invitation, Week 1 expectations)

**Deliverables:**
- Kickoff summary email (recap, action items, timeline)
- Student invitation email template (personalized for university)
- Crisis contact form (completed, verified)
- Week 1 expectations document (what to expect, how to measure)

### Post-Kickoff Actions (Day 2-3)

**Configure University in System:**
```python
# Add university record
INSERT INTO universities (id, name, domain, caps_email, caps_phone, waitlist_weeks)
VALUES (2, 'University of Michigan', 'umich.edu', 'caps@umich.edu', '+1234567890', 8);

# Add counselor contacts
INSERT INTO university_counselors (university_id, name, email, phone, role, alert_methods)
VALUES (2, 'Dr. Jane Smith', 'jsmith@umich.edu', '+1234567890', 'Director', 'email,sms');

# Configure crisis resources (if university-specific)
INSERT INTO resources (title, description, url, category, university_id)
VALUES ('UMich CAPS Crisis Line', '24/7 crisis support', 'tel:+1234567890', 'crisis', 2);
```

**Prepare Student Invitation:**
- Customize template (university name, CAPS director name, waitlist length)
- Add university branding (logo, colors - if custom branding feature exists)
- Test email (send to founder, verify formatting, links work)

**Technical Verification:**
- Test crisis alert delivery (trigger keyword, verify email/SMS sent)
- Verify university ID in database
- Test student signup flow (ensure university-specific resources shown)

## Week 2: Student Invitation & Launch

### Student Invitation (Day 1)

**Director Sends Email:**
```
Subject: Immediate support while you wait for your CAPS appointment

Hi [First Name],

You're on the CAPS waitlist, and we know waiting can be hard (currently [X] weeks). 
We want to support you NOW, not just when your appointment arrives.

We're piloting GentleQuest - a 24/7 AI chatbot designed specifically for students 
waiting for counseling. Think of it as a supportive friend who's always available 
to listen and help you manage stress.

✅ Anonymous (CAPS doesn't track what you say)
✅ Free (no cost to you)
✅ 24/7 (available anytime, especially late nights)
✅ Evidence-based (uses proven CBT/DBT techniques)

Your CAPS appointment is still scheduled - this is support WHILE you wait, 
not instead of counseling.

Ready to try it? Sign up in 2 minutes: [SIGNUP LINK]

Questions? Reply to this email.

[CAPS DIRECTOR NAME]
Director, Counseling & Psychological Services
[UNIVERSITY NAME]
```

**Monitoring Signup Rate (Day 1-3):**
- Target: 30% signup within 3 days
- If <20% by Day 3: Offer to resend with revised messaging
- Track: Invited (count), signed up (count), signup rate (%)

### Early Engagement Monitoring (Day 4-7)

**Daily Checks:**
- Active users (how many chatting, logging mood, completing quests)
- First session quality (review 5-10 random conversations)
- Technical issues (errors, slow responses, bugs)
- Crisis events (any detected, CAPS notified, response time)

**Week 1 Report (Friday):**
```
Week 1 Update - [UNIVERSITY]

INVITATION:
• Invited: [X] students
• Signed up: [Y] ([Z]%) ✅/⚠️
• Target: 30%+

ENGAGEMENT:
• Active this week: [A] ([B]% of signups) ✅/⚠️
• Avg sessions per user: [C]
• Target: 40%+ weekly active

FIRST IMPRESSIONS:
• Students finding Luna warm and supportive ✅
• [X] students mentioned [FEEDBACK]
• [Y] technical issues identified (investigating)

SAFETY:
• Crisis events: [N]
• All detected ✅
• CAPS notified within 5 min ✅

NEXT WEEK:
• Monitor engagement (target 40%+ weekly active)
• Address [ISSUE] if any
• Continue daily monitoring

Questions? Call me: [PHONE]
```

## Week 3: Steady State Monitoring

### Weekly Report Cadence

**Every Friday 5pm:**
- Generate report (engagement, outcomes, crisis events, trends)
- Add personal note (observations, concerns, celebrations)
- Send to director (email, consistent format)
- Log in CRM (notes, next steps, health score)

**Bi-Weekly Check-In Calls (15 min):**
- Week 2: "How's it going? Any concerns?"
- Week 4: "Engagement looks good/concerning, here's why..."
- Week 6: Mid-pilot review (30 min, formal)
- Week 8: "On track for Week 12 results presentation"
- Week 10: "Preparing final data, any questions?"

### Health Monitoring

**Green (Healthy):**
- Engagement 40%+ weekly active ✅
- No major student complaints ✅
- Director responsive (<48 hours) ✅
- Crisis events handled well ✅

**Yellow (At-Risk):**
- Engagement 30-40% ⚠️
- 1-2 student complaints ⚠️
- Director slow to respond (3-5 days) ⚠️
- Minor technical issues ⚠️

**Red (Intervention Needed):**
- Engagement <30% 🔴
- Multiple student complaints 🔴
- Director ghosting (>5 days) 🔴
- Crisis event missed 🔴

**Action by Status:**
- Green: Continue, celebrate wins
- Yellow: Schedule call, address concerns proactively
- Red: Activate rescue protocol (see PILOT_TROUBLESHOOTING_RESCUE.md)

## Onboarding Checklist

### Pre-Kickoff
- [ ] Contract signed, payment terms agreed
- [ ] University ID assigned in database
- [ ] Kickoff call scheduled (1 hour, within 7 days)
- [ ] Kickoff materials prepared (agenda, templates, forms)

### Kickoff Call
- [ ] Introductions completed
- [ ] Expectations aligned (targets, timeline, success criteria)
- [ ] Logistics confirmed (invitation process, crisis protocol)
- [ ] Technical demo (platform access, crisis alert test)
- [ ] Q&A addressed (concerns, questions, next steps)

### Post-Kickoff
- [ ] Kickoff summary email sent (same day)
- [ ] University configured in system (ID, counselors, resources)
- [ ] Student invitation template customized
- [ ] Crisis alert tested and verified

### Week 1
- [ ] Student invitation sent (Day 1)
- [ ] Signup rate monitored (target 30% by Day 3)
- [ ] Early engagement monitored (daily checks Day 4-7)
- [ ] Week 1 report sent (Friday 5pm)

### Week 2-12
- [ ] Weekly reports sent (every Friday 5pm)
- [ ] Bi-weekly check-in calls (Week 2, 4, 8, 10)
- [ ] Mid-pilot review (Week 6, 30 min)
- [ ] Health monitoring (Green/Yellow/Red status)
- [ ] Intervention if needed (Yellow/Red status)

### Week 12
- [ ] Final data compiled (engagement, outcomes, satisfaction)
- [ ] Results presentation prepared (deck, data, testimonials)
- [ ] Results call scheduled (30 min)
- [ ] Conversion discussion (paid contract or end pilot)

## Common Onboarding Issues

### Issue 1: Low Signup Rate (<20%)

**Diagnosis:**
- Invitation email not compelling
- Too many steps to sign up
- Timing (finals week, break)
- Wrong audience (not actually on waitlist)

**Fix:**
- Rewrite invitation (clearer value prop, urgency)
- Simplify signup (reduce to 3 fields max)
- Resend at better time (Week 2-4 of semester)
- Verify audience (actually on waitlist, engaged with CAPS)

### Issue 2: Technical Issues (Slow Response, Errors)

**Diagnosis:**
- AI provider timeout
- Database connection issues
- Frontend bugs

**Fix:**
- Check logs (identify root cause)
- Deploy hotfix (within 24 hours if critical)
- Communicate to director (transparency, timeline)

### Issue 3: Director Unresponsive

**Diagnosis:**
- Too busy (semester start, crisis on campus)
- Not seeing value (engagement low, outcomes not there yet)
- Communication breakdown (emails going to spam, wrong contact)

**Fix:**
- Call directly (don't just email)
- Adjust communication (less frequent if too much, more if too little)
- Demonstrate value (share early wins, student testimonials)

## Onboarding Success Metrics

**Week 1:**
- Signup rate: 30%+ ✅
- Active users: 40%+ of signups ✅
- Director satisfaction: 7+/10 ✅

**Week 4:**
- Weekly active: 40%+ sustained ✅
- Retention: 50%+ Week 1 users still active ✅
- Director engagement: Responds <48 hours ✅

**Week 12:**
- Engagement: 40%+ weekly active ✅
- Outcomes: 20%+ symptom reduction ✅
- Satisfaction: 75%+ students, 7+/10 director ✅
- Conversion: Pilot → paid contract ✅

**Onboarding complete when pilot converts to paid contract (30% conversion rate target)**
