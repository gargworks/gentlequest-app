# B2B Dashboard Spec: "The Counselor's Lens"

**Product Goal:** Provide University Counseling Directors with the aggregate data they need to justify GentleQuest's budget and improve campus safety.

---

## 1. The Core Metrics (What the Director Needs)

| Metric | Why it Matters | GentleQuest Data Source |
| :--- | :--- | :--- |
| **Reach / Penetration** | "What % of our 20k students are actually using this?" | Active Users / Total Enrollment. |
| **The "2 AM" Usage** | Proves the app is handling the "after-hours" void. | Heatmap of usage hours (Focus on 10 PM - 4 AM). |
| **Symptom Reduction** | Clinical proof of ROI. | Aggregate change in PHQ-9 (Depression) and GAD-7 (Anxiety) scores. |
| **Top Stressors** | "Are students stressed about midterms or social isolation?" | NLP Tagging of anonymous journal themes (e.g., "Exam stress", "Loneliness"). |
| **Crisis Interventions** | The "Safety" proof. | Total C-SSRS screeners triggered + Successful handshakes to On-Call. |

---

## 2. Competitive Edge: The "Staffing Relief" Index
University Directors are obsessed with **CLI (Clinical Load Index)**—the ratio of counselors to students.
*   **The Problem:** Counselors are burned out.
*   **The GentleQuest Solution:** A dashboard widget that shows **"Hours of Human Counseling Saved."**
    *   *Calculation:* (Total AI Minutes Spent on Quests / 50 minute session equivalent).
    *   *Message:* "GentleQuest provided 450 hours of support this month, equivalent to adding 2.5 full-time counselors."

---

## 3. Privacy & Compliance (B2B Table Stakes)
*   **Anonymized by Default:** Individual journal entries are NEVER visible.
*   **Threshold Reporting:** If a specific sub-group (e.g., "Engineering Students") has < 10 users, data is hidden to prevent re-identification.
*   **HIPAA/FERPA Ready:** Data hosted on encrypted, single-tenant instances if required by the university.

---

## 4. Feature: "The Campus Mood Alert"
A weekly automated email to the Director:
> "Hello Dr. Miller, 
> 🏮 **Warning:** We've detected a 14% spike in 'Academic Anxiety' keywords this week compared to last. 
> 💡 **Recommendation:** Consider sending a campus-wide 'Gentle Nudge' about burnout before finals."

---

## 5. Next Steps for Implementation
1.  **Phase 1:** Build the "Aggregate Mood" charts using dummy data.
2.  **Phase 2:** Implement the PHQ-9/GAD-7 tracking backend logic.
3.  **Phase 3:** Create the "Counselor Handshake" log for liability protection.
