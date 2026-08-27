# 🗺️ GentleQuest Product Roadmap (2026)

> **Mission:** To build the most effective, "anti-productivity" mental health assistant for the ADHD/Burnout generation.

---

## 🛤️ Track 1: Market Entry ("The Sensor Network")
**Owner:** Marketing Agent (Comet)  
**Goal:** Acquire users via "Anti-Productivity" positioning.

### Phase 1.1: The Quiet Launch (Current)
- [ ] **IndieHackers:** "Roast my App" post (Draft ready).
- [ ] **Reddit:** "Standard productivity apps make my ADHD worse" (Draft ready).
- [ ] **Method:** Manual posting -> Automated listening.

### Phase 1.2: The Growth Loop (Next)
- [ ] **Inbox Listener:** Connect Comet (Browser) to Nucleus. Auto-detect replies and draft responses.
- [ ] **Trends:** Daily scan of r/ADHD and Twitter for "Burnout" spikes to trigger content creation.

### Phase 1.3: Community
- [ ] **Discord/Telegram:** Private "Quiet Club" for power users.

---

## 🛡️ Track 2: Product Hardening ("The Sticky App")
**Owner:** Lead Systems Architect  
**Goal:** Retention & Reliability.

### Phase 2.1: Identity (Priority 1)
*Currently, users are anonymous and tied to browser sessions.*
- [ ] **Authentication:** Firebase or Supabase Auth.
- [ ] **Profile Sync:** Link data across Desktop and Mobile.
- [ ] **Anonymous-to-Registered:** Frictionless upgrade path to save data.

### Phase 2.2: Ubiquity (Priority 2)
- [ ] **Mobile Apps:** Compile existing Flutter codebase for iOS (TestFlight) and Android (APK).
- [ ] **Notifications:** Local push notifications for "Gentle Nudges" (not spammy).
- [ ] **Offline Mode:** PWA Service Workers to allow journaling without internet.

### Phase 2.3: Performance
- [ ] **Redis Caching:** Sub-millisecond session retrieval.
- [ ] **Edge Deployment:** Move static assets to CDN.

---

## 🩺 Track 3: Clinical Depth ("The Value")
**Owner:** Product Manager & Clinical Advisor  
**Goal:** High value, evidence-based outcomes.

### Phase 3.1: Assessments
- [ ] **PHQ-9 (Depression):** Standardized screener.
- [ ] **GAD-7 (Anxiety):** Standardized screener.
- [ ] **Visual Tracking:** Graph scores over time (confetti for stability, not just improvement).

### Phase 3.2: Crisis Protocols (B2B Prep)
- [ ] **Real-time Classification:** Upgrade Safety Layer to detect implicit suicidal ideation.
- [ ] **Escalation Path:** "Click here to call [Local Hotline]" (Geo-located).
- [ ] **Therapist Export:** Single-click PDF export of "Last 30 Days" for doctors.

---

## 🔮 Track 4: The Vision (Long Term)

### 4.1 Multi-Modal Journaling
- **Voice:** "Just vent for 2 minutes" -> AI summarizes & tags emotions.
- **Image:** "Photo of my messy room" -> AI gives ONE tiny step to clean it.

### 4.2 B2B/Enterprise
- White-label for Universities (Student Wellness).
- White-label for Corporate (Employee Assistance).
