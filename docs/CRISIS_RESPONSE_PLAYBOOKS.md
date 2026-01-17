# Crisis Response Playbooks - Real-World Scenarios
## Detailed Procedures for Every Crisis Type

## Scenario 1: Suicide Mention During Chat

### Detection
**Student Message:** "I want to kill myself, I can't take it anymore"

**System Response (Automatic):**
1. Crisis detection triggered (keyword: "kill myself")
2. Risk level: CRITICAL
3. Crisis resources displayed (988, campus hotline, Crisis Text Line)
4. CAPS alert created (within 5 seconds)
5. Email sent to counselor (within 30 seconds)
6. SMS sent to counselor (if CRITICAL + SMS enabled)

### Counselor Response Protocol

**Within 5 Minutes:**
- [ ] Check email/SMS alert
- [ ] Review student context (session ID, conversation excerpt, keywords)
- [ ] Assess severity (imminent? plan? means?)

**Within 15 Minutes:**
- [ ] Contact student (call, email, or campus security if imminent)
- [ ] Verify student safety (are they safe right now?)
- [ ] Schedule emergency appointment (same day or next day)

**Within 1 Hour:**
- [ ] Acknowledge alert in CAPS dashboard
- [ ] Document response (what action taken, student status)
- [ ] Follow-up plan (daily check-ins until seen by counselor)

**Within 24 Hours:**
- [ ] Verify student attended appointment (or scheduled)
- [ ] Update GentleQuest (alert acknowledged, action documented)
- [ ] Debrief (what worked, what didn't, improvements)

### Founder Response Protocol

**Within 5 Minutes:**
- [ ] Verify alert sent (check SendGrid dashboard, email delivery)
- [ ] Monitor for acknowledgment (counselor should respond <15 min)

**Within 30 Minutes:**
- [ ] If no acknowledgment: Call CAPS director directly
- [ ] If no answer: Call backup contact
- [ ] Escalate until someone responds

**Within 24 Hours:**
- [ ] Follow up with director (student safe? action taken?)
- [ ] Document in crisis log (for audit trail, legal protection)
- [ ] Review detection (was it accurate? any improvements?)

### Post-Crisis Actions

**Within 1 Week:**
- [ ] Debrief with director (what worked, what didn't)
- [ ] Update crisis protocol (if gaps identified)
- [ ] Student follow-up (is student still using GentleQuest? attending therapy?)

**Within 1 Month:**
- [ ] Review all crisis events (patterns, improvements)
- [ ] Clinical advisor review (were responses appropriate?)
- [ ] Update keyword list (if any missed variations)

---

## Scenario 2: Self-Harm Disclosure

### Detection
**Student Message:** "I've been cutting myself every night this week"

**System Response:**
1. Crisis detection: HIGH risk
2. Resources displayed (crisis hotlines, self-harm resources)
3. CAPS alert created (email sent within 30 seconds)
4. No SMS (not CRITICAL level)

### Counselor Response Protocol

**Within 1 Hour:**
- [ ] Check email alert
- [ ] Review student context
- [ ] Assess severity (frequency, depth, infection risk)

**Within 4 Hours:**
- [ ] Contact student (call or email)
- [ ] Verify safety (are cuts infected? need medical care?)
- [ ] Schedule appointment (within 48 hours)

**Within 24 Hours:**
- [ ] Acknowledge alert
- [ ] Document response
- [ ] Follow-up plan (weekly check-ins for 4 weeks)

### Student Support Plan

**Immediate:**
- Luna provides grounding techniques (5-4-3-2-1, breathing)
- Resources shown (self-harm alternatives, coping strategies)
- Encouragement to reach out (CAPS, trusted person, crisis line)

**Ongoing:**
- Daily check-ins (Luna asks "How are you today?")
- Mood tracking (monitor for worsening)
- Quest reminders (healthy coping alternatives)

**Transition:**
- CAPS appointment (warm handoff, Luna encourages attendance)
- Continue using GentleQuest (supplement to therapy, not replacement)

---

## Scenario 3: Harm to Others Threat

### Detection
**Student Message:** "I'm planning to hurt my roommate, I can't control my anger"

**System Response:**
1. Crisis detection: CRITICAL
2. Resources displayed (crisis hotlines, anger management)
3. CAPS alert created (immediate)
4. Email + SMS sent (CRITICAL level)
5. **Additional:** Campus security notified (if protocol exists)

### Counselor Response Protocol

**Immediate (Within 5 Minutes):**
- [ ] Check alert
- [ ] Assess threat (specific? imminent? means?)
- [ ] Contact campus security (if imminent threat)
- [ ] Contact student (verify safety of student and potential victim)

**Within 15 Minutes:**
- [ ] Threat assessment (is roommate in danger?)
- [ ] Protective action (separate student and roommate if needed)
- [ ] Emergency appointment (same day, mandatory)

**Within 1 Hour:**
- [ ] Notify dean of students (threat to campus safety)
- [ ] Document thoroughly (legal protection, threat assessment)
- [ ] Coordinate with campus security (ongoing monitoring)

### Legal Considerations

**Duty to Warn:**
- If specific, credible threat to identifiable person → Must warn potential victim
- Tarasoff duty (legal requirement in most states)
- Consult university legal counsel

**Documentation:**
- Detailed notes (what student said, when, what action taken)
- Threat assessment (severity, imminence, means, intent)
- Actions taken (who notified, when, outcome)

---

## Scenario 4: Crisis Event Missed (Worst Case)

### Detection
**Situation:** Student mentioned suicide, alert NOT sent (system failure)

**How Discovered:**
- Student reports ("I mentioned suicide, no one called")
- CAPS reports ("We weren't notified")
- Internal monitoring (alert should have sent, didn't)

### Immediate Response (Hour 0-1)

**Founder Actions:**
- [ ] Verify student safe (call CAPS, confirm student contacted)
- [ ] Apologize (to student, to CAPS, take full responsibility)
- [ ] Investigate (why didn't alert send? bug? config error? external service failure?)
- [ ] Preserve evidence (logs, database records, don't delete)

**CAPS Actions:**
- [ ] Contact student immediately (verify safety)
- [ ] Emergency appointment (same day if possible)
- [ ] Document incident (for university records, potential liability)

### Short-Term Response (Hour 1-24)

**Founder Actions:**
- [ ] Identify root cause (code bug, SendGrid failure, database issue)
- [ ] Deploy hotfix (within 24 hours)
- [ ] Test extensively (verify fix works, no regression)
- [ ] Document (post-mortem, what happened, why, prevention)

**CAPS Actions:**
- [ ] Follow up with student (daily check-ins until stable)
- [ ] Report to dean (incident, response, outcome)
- [ ] Evaluate GentleQuest (continue or pause pilot)

### Long-Term Response (Day 2-30)

**Founder Actions:**
- [ ] Notify all partners (transparency, what happened, what we fixed)
- [ ] Offer compensation (credit, extended pilot, refund if appropriate)
- [ ] Update crisis protocol (add redundancy, improve monitoring)
- [ ] Third-party audit (if appropriate, verify fix)

**CAPS Actions:**
- [ ] Decision (continue pilot, pause, or end)
- [ ] If continue: Enhanced monitoring (daily check-ins with founder)
- [ ] If end: Graceful offboarding (student transition, data deletion)

### Legal/Insurance

**Immediate:**
- [ ] Notify professional liability insurance carrier
- [ ] Consult lawyer (don't respond publicly without legal advice)
- [ ] Preserve all evidence (logs, emails, contracts)

**If Lawsuit:**
- [ ] Insurance defense (carrier provides lawyer)
- [ ] Cooperate fully (provide requested documents)
- [ ] Settlement discussions (if appropriate)

**Prevention:**
- [ ] Comprehensive testing (crisis scenarios in every deploy)
- [ ] Redundancy (backup alert method if primary fails)
- [ ] Monitoring (alert delivery tracking, automatic retry)

---

## Scenario 5: Student Suicide (Worst-Case)

### If Student Using GentleQuest Dies by Suicide

**Immediate (Hour 0-24):**
- [ ] Verify facts (CAPS director confirms, police report if available)
- [ ] Review logs (did student mention suicide? was alert sent? was CAPS notified?)
- [ ] Legal counsel (call lawyer immediately, don't respond publicly)
- [ ] Insurance (notify professional liability carrier)
- [ ] Preserve evidence (logs, emails, contracts, don't delete anything)

**Short-Term (Day 2-7):**
- [ ] Investigate (what happened? could we have prevented?)
- [ ] Cooperate (with university, police, regulators)
- [ ] Support (offer condolences to family, university - through lawyer)
- [ ] Internal review (crisis protocol, improvements needed)
- [ ] Notify partners (transparency with other universities)

**Long-Term (Week 2+):**
- [ ] Legal defense (if sued, work with lawyer and insurance)
- [ ] Protocol improvements (update crisis detection, add redundancy)
- [ ] Transparency (if appropriate, share learnings publicly)
- [ ] Rebuild trust (demonstrate improvements, safety commitment)

**Communication:**
- **Internal:** "We are devastated. Cooperating fully with investigation. Reviewing protocols."
- **Public (if required):** "GentleQuest is committed to student safety. We are reviewing circumstances and working with [UNIVERSITY] to understand what happened. We will share learnings to improve mental health support."
- **Tone:** Somber, empathetic, responsible (not defensive)

**Probability:** <1% (with 100% crisis detection, immediate CAPS escalation)

---

## Scenario 6: Data Breach

### If Student Conversations Exposed

**Immediate (Hour 0-4):**
- [ ] Isolate affected systems (disable access, block IP)
- [ ] Investigate (what data exposed? how many students?)
- [ ] Preserve evidence (logs, access records)
- [ ] Legal counsel (call lawyer, don't notify yet without advice)

**Short-Term (Hour 4-72):**
- [ ] Remediate (fix vulnerability, verify fix)
- [ ] Notify affected students (email, within 72 hours GDPR)
- [ ] Notify universities (CAPS directors, transparency)
- [ ] Notify regulators (if required: FTC, state AG, OCR)
- [ ] Public disclosure (if >500 affected, some states require)

**Long-Term (Week 2+):**
- [ ] Post-mortem (what happened, why, prevention)
- [ ] Security improvements (penetration test, additional controls)
- [ ] Rebuild trust (transparency, demonstrate improvements)
- [ ] Insurance claim (cyber liability coverage)

**Communication:**
- **To Students:** "We discovered a data security incident on [DATE]. Your [WHAT DATA] may have been accessed. We immediately [ACTIONS]. We sincerely apologize and are offering [SUPPORT]."
- **To Universities:** "We experienced a data security incident affecting [N] students. We have contained it, notified affected users, and implemented additional security. Full transparency: [DETAILS]."
- **Tone:** Transparent, apologetic, action-oriented (not minimizing)

---

## Scenario 7: Mass Crisis Event (Campus Tragedy)

### If Multiple Students in Crisis Simultaneously

**Trigger:** Campus tragedy (suicide, shooting, natural disaster)

**System Response:**
- Multiple crisis alerts (10-50+ students mention crisis keywords)
- CAPS overwhelmed (can't respond to all immediately)
- System load (high traffic, many concurrent users)

### Founder Response

**Immediate (Hour 0-4):**
- [ ] Monitor system (can it handle load? any performance issues?)
- [ ] Scale if needed (increase server capacity)
- [ ] Coordinate with CAPS (prioritize most severe alerts)
- [ ] Offer additional support (extend pilot, waive fees, whatever helps)

**Short-Term (Day 1-7):**
- [ ] Daily check-ins with CAPS (how can we help?)
- [ ] System monitoring (24/7, ensure no downtime)
- [ ] Flexible reporting (daily instead of weekly if needed)
- [ ] Community support (if community feature exists, moderate carefully)

**Long-Term (Week 2+):**
- [ ] Debrief with CAPS (what worked, what didn't)
- [ ] System improvements (handle mass crisis events better)
- [ ] Relationship deepening (university remembers we were there when needed)

### CAPS Response

**Immediate:**
- [ ] Triage alerts (most severe first)
- [ ] Activate crisis team (all counselors on deck)
- [ ] Campus-wide response (coordinate with dean, security, communications)

**GentleQuest Role:**
- Provide immediate support (24/7, when CAPS can't see everyone)
- Identify highest-risk students (alert prioritization)
- Reduce CAPS burden (students get some support, not zero)

---

## Crisis Metrics & Monitoring

### Real-Time Monitoring

**Dashboard Metrics:**
- Pending alerts (count, severity, age)
- Response time (alert sent → acknowledged, target <1 hour)
- Detection rate (crises detected ÷ crises total, target 100%)
- False positive rate (false alarms ÷ total alerts, target <5%)

**Alert Thresholds:**
- Pending alerts >5: Notify founder
- Response time >2 hours: Call CAPS director
- Detection failure: Immediate investigation
- False positive rate >10%: Review keyword list

### Weekly Crisis Review

**Every Monday:**
- [ ] Review all crisis events from past week
- [ ] Verify all were handled (acknowledged, action taken)
- [ ] Identify patterns (time of day, keywords, student demographics)
- [ ] Update protocol (if improvements needed)

### Monthly Crisis Audit

**Every Month:**
- [ ] Clinical advisor review (sample 10 crisis conversations)
- [ ] Detection accuracy (any missed? any false positives?)
- [ ] Response time analysis (average, p95, outliers)
- [ ] Protocol improvements (based on learnings)

---

## Crisis Communication Templates

### To Student (If Appropriate)

```
Hi [Student],

We noticed you mentioned [CRISIS KEYWORD] in your conversation with Luna. 
We want you to know:

1. You're not alone. Help is available 24/7.
2. Your CAPS counselor has been notified and will reach out soon.
3. If you're in immediate danger, please call 988 or campus security.

We care about you and want you to be safe.

- GentleQuest Team
```

### To CAPS Director (Alert Email)

```
Subject: [CRITICAL] Student Crisis Alert - GentleQuest

Dr. [Director],

A student using GentleQuest mentioned suicide. Details:

Time: [TIMESTAMP]
Session ID: [ID]
Trigger: "[STUDENT MESSAGE]"
Keywords: [DETECTED KEYWORDS]

Recent conversation:
[EXCERPT]

RECOMMENDED ACTION:
• Contact student immediately
• Verify safety
• Schedule emergency appointment

View full alert: [DASHBOARD LINK]

This is an automated alert. For support: [FOUNDER PHONE]

- GentleQuest Crisis Alert System
```

### To University (If Crisis Missed)

```
Subject: Incident Report - Missed Crisis Alert

Dr. [Director],

I'm writing to inform you of a serious incident. On [DATE], a student mentioned 
suicide in GentleQuest, but our alert system failed to notify you.

WHAT HAPPENED:
[Technical explanation]

IMMEDIATE ACTIONS TAKEN:
• Verified student safety (contacted CAPS)
• Identified root cause (bug in alert delivery)
• Deployed fix (within 24 hours)
• Added redundancy (backup alert method)

PREVENTION:
• Enhanced monitoring (alert delivery tracking)
• Increased testing (crisis scenarios in every deploy)
• Third-party audit (if appropriate)

I take full responsibility. Student safety is our top priority, and we failed. 
I'm committed to ensuring this never happens again.

Available to discuss: [PHONE]

Sincerely,
[YOUR NAME]
Founder, GentleQuest
```

---

## Crisis Training

### For Founder

**Quarterly Drills:**
- [ ] Simulate crisis event (test alert delivery)
- [ ] Practice response (call CAPS, verify received)
- [ ] Time response (should be <5 min alert, <30 min verification)
- [ ] Document (what worked, what didn't, improvements)

**Annual Review:**
- [ ] Review all crisis events from year
- [ ] Calculate metrics (detection rate, response time, outcomes)
- [ ] Update protocol (based on learnings)
- [ ] Clinical advisor review (are we handling appropriately?)

### For CAPS Directors

**Onboarding Training:**
- [ ] Crisis protocol walkthrough (how alerts work, what to expect)
- [ ] Dashboard training (how to view alerts, acknowledge, respond)
- [ ] Practice drill (send test alert, verify they receive and respond)

**Ongoing:**
- [ ] Quarterly check-ins (any issues with alerts? improvements needed?)
- [ ] Annual review (crisis events, response times, outcomes)

---

## Crisis Escalation Matrix

| Severity | Response Time | Action | Notification |
|----------|---------------|--------|--------------|
| **CRITICAL** | <5 min | Contact student immediately, campus security if needed | Email + SMS |
| **HIGH** | <1 hour | Contact student, schedule emergency appointment | Email |
| **MEDIUM** | <24 hours | Contact student, prioritize for next appointment | Email |
| **LOW** | Monitor | No immediate action, track in system | None |

## Crisis Outcome Tracking

### Metrics to Track

**For Each Crisis Event:**
- Detection time (when student mentioned crisis)
- Alert sent time (when CAPS notified)
- Acknowledgment time (when counselor responded)
- Resolution time (when student contacted, appointment scheduled)
- Outcome (student safe, appointment attended, ongoing support)

**Aggregate Metrics:**
- Detection rate (target 100%)
- Alert delivery rate (target 100%)
- Response time (target <1 hour average)
- Resolution rate (target 100% students contacted)
- Outcome (target 0 student harm)

### Success Criteria

**System Performance:**
- ✅ 100% detection rate (no missed crises)
- ✅ 100% alert delivery (all counselors notified)
- ✅ <5 min alert delivery time
- ✅ <1 hour average response time (counselor → student)
- ✅ 0 student harm (no suicides, no serious self-harm)

**If Any Metric Fails:**
- Immediate investigation
- Root cause analysis
- Protocol improvement
- Enhanced monitoring

**Crisis response playbooks complete. 7 scenarios: Suicide mention (5 min alert, 15 min contact, 1 hour acknowledge), self-harm (1 hour alert, 4 hour contact), harm to others (immediate, campus security), crisis missed (investigate, fix, notify), student suicide (legal, investigate, improve), data breach (isolate, notify 72 hours), mass crisis (scale, coordinate, support). Response protocols: Counselor (verify, contact, document), founder (monitor, escalate, follow-up). Communication templates: Student, CAPS director, university. Training: Quarterly drills, annual review. Escalation matrix: CRITICAL <5 min, HIGH <1 hour, MEDIUM <24 hours. Outcome tracking: Detection 100%, delivery 100%, response <1 hour, resolution 100%, harm 0.**
