# GentleQuest v1.4.0 Regional Compliance Matrix

## Goal
The goal of this compliance matrix is to define the strict legal, privacy, and regulatory boundaries for GentleQuest as a consumer mental health application across six major global jurisdictions. This matrix directly informs the logic for the ComplianceGuard dynamic gating system (v1.4.0 PRD Item #2), ensuring we legally operate as a peer-support wellness app while preventing exposure to severe fines for violations of age-of-consent, data residency, breach notification, and medical device regulations.

## Matrix

| Jurisdiction | Key Law(s) | Min Age for Digital Consent | Mental Health App Classification (Medical Device?) | Data Residency Requirements | Breach Notification Threshold | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **US** | HIPAA, COPPA, State Laws (IL MHDDCA, CA, NY, TX, WA, UT) | 13 | No (if wellness/peer support) | None (federal), but local storage preferred | >500 users within 60 days (HIPAA); varies by state | **Gate** (Age 13+, state-by-state toggles) |
| **India** | DPDP Act 2023 | 18 | No | Cross-border allowed unless blacklisted | Without delay / 72 hours to DPBI | **Explicit Ban** (for <18 without parental flow) |
| **EU** | GDPR, AI Act | 13-16 (varies by member state) | No (if not diagnosing/treating) | EEA preferred; cross-border requires adequacy/SCCs | 72 hours to DPA if risk to rights/freedoms | **Gate** (Age 16+ pan-EU, explicit Article 9 consent) |
| **UK** | UK GDPR, ICO AADC, Online Safety Act | 13 | No (if not diagnosing/treating) | UK/EEA preferred; adequacy needed for others | 72 hours to ICO if risk to rights/freedoms | **Gate** (Age 13+, AADC Privacy-by-Default) |
| **Australia**| Privacy Act 1988 (APPs), TGA Guidelines | 15 (Guidelines) | No (Excluded under Item 14E) | Onshore (Australia) strongly expected for health data | 30 days to OAIC for "serious harm" (NDB scheme) | **Allow / Gate** (Onshore storage required) |
| **Canada** | PIPEDA, Provincial Laws (e.g., PHIPA) | No fixed age (Under 13 needs parent) | No | Cross-border allowed but must protect to PIPEDA std | Real risk of significant harm (RROSH) | **Gate** (Age 13+, express consent) |

## Per-Jurisdiction Sections

### United States
**Summary:** The US landscape is highly fragmented. While COPPA sets a hard floor of 13 for digital consent, health data is governed by a patchwork of federal (HIPAA, if a covered entity) and state laws. State laws like Illinois' MHDDCA, Washington's My Health My Data Act, and comprehensive privacy laws in CA, UT, and TX impose strict requirements on biometric and mental health data. Breach notification timelines and thresholds vary wildly by state.
**Recommended Action:** **Gate.** Hard block users under 13 globally. Implement state-by-state dynamic gating to disable the app in high-risk states (e.g., IL, WA) unless specific compliance modules are met.
**Uncertainty Notes (Legal Review Needed):** We need legal counsel to verify if GentleQuest operates strictly outside the definition of a HIPAA "Covered Entity" or "Business Associate," and to confirm which specific US states require immediate geo-blocking due to aggressive private rights of action.

### India
**Summary:** The Digital Personal Data Protection (DPDP) Act 2023 defines a child as anyone under 18 and mandates verifiable parental consent for processing their data. While data localization is not strictly enforced (cross-border transfers are allowed unless explicitly blacklisted), breach notification has no materiality threshold and must be reported within 72 hours.
**Recommended Action:** **Explicit Ban** for users under 18. Until a scalable Aadhaar/DigiLocker parental consent flow is built, any user identifying as under 18 in India must be hard-blocked from the service.
**Uncertainty Notes (Legal Review Needed):** Determine if a mental health wellness app qualifies us as a "Significant Data Fiduciary" under DPDP, which would trigger mandatory DPIAs and the appointment of an India-based Data Protection Officer.

### European Union
**Summary:** Under the GDPR, mental health data is classified as Article 9 "Special Category Data," requiring explicit, granular, and easily revocable consent. The age of digital consent varies by member state (between 13 and 16). The upcoming AI Act also strictly regulates AI systems, though basic wellness chatbots may avoid high-risk medical device classification if they do not diagnose or treat.
**Recommended Action:** **Gate.** Implement a conservative pan-EU age gate of 16+. Require a dedicated, unbundled consent modal specifically for "processing sensitive mental health conversation data" before onboarding.
**Uncertainty Notes (Legal Review Needed):** Verify that our LLM-based responses do not inadvertently cross the threshold into "medical device" territory under the EU Medical Device Regulation (MDR) or the AI Act's high-risk categories.

### United Kingdom
**Summary:** The UK GDPR mirrors EU law by treating health data as Special Category Data. The age of consent is firmly set at 13. Crucially, the ICO's Age Appropriate Design Code (AADC) mandates that services likely to be accessed by children must have "Privacy by Default" settings (e.g., no behavioral tracking, highest privacy settings enabled automatically).
**Recommended Action:** **Gate.** Allow 13+, but ensure the entire onboarding flow and default telemetry settings comply with the AADC. Obtain explicit Article 9 consent for health data.
**Uncertainty Notes (Legal Review Needed):** Assess our obligations under the new Online Safety Act 2023 regarding the proactive shielding of minors from harmful content (e.g., self-harm discussions), balancing privacy with safeguarding duties.

### Australia
**Summary:** The Therapeutic Goods Administration (TGA) excludes general mental health/wellness apps from medical device regulation (under Item 14E) provided they do not screen, diagnose, or treat. However, under the Privacy Act, mental health data is "sensitive information," triggering the Notifiable Data Breaches (NDB) scheme for almost any breach. Australian privacy principles carry a very strong expectation that health data remains onshore.
**Recommended Action:** **Allow / Gate.** We can operate without TGA approval, but we must strongly consider routing Australian user data to an onshore AWS/GCP region (data residency gating) to comply with APP health data expectations.
**Uncertainty Notes (Legal Review Needed):** Confirm if our current cloud infrastructure (which may route data to US servers) violates the APP 8 cross-border disclosure rules for sensitive health information without explicit, risk-acknowledged user consent.

### Canada
**Summary:** PIPEDA treats health data as highly sensitive, requiring express (opt-in) consent rather than implied consent. There is no hard statutory age of consent; instead, it relies on the concept of "meaningful consent" based on maturity, though the OPC considers <13 impossible to consent. Provincial laws (like Ontario's PHIPA) may impose stricter health data rules.
**Recommended Action:** **Gate.** Allow 13+, provided the consent flow is written in plain language suitable for adolescents. Ensure express opt-in for health data processing.
**Uncertainty Notes (Legal Review Needed):** Clarify the intersection of federal PIPEDA and strict provincial health privacy laws (e.g., PHIPA, Quebec's Law 25) regarding our specific data collection model.

## Open Questions for Legal Counsel
1. **Medical Device Boundary:** At what point does a generative AI "peer support" response cross the line into "diagnosis, treatment, or screening" under FDA (US), TGA (AUS), and MDR (EU) guidelines?
2. **US State Geo-Blocking:** Which US states have health privacy laws with Private Rights of Action (like Illinois MHDDCA) that require immediate geo-blocking to avoid ruinous class-action liability?
3. **India DPDP:** Does our volume or data type automatically classify us as a Significant Data Fiduciary in India?
4. **Data Residency (AUS/EU):** Are we legally permitted to process Australian and EU mental health data on US-based LLM inference servers if we obtain explicit cross-border transfer consent, or is localized inference strictly mandated?

## Reference Designs Cross-Links
* This matrix directly drives the implementation of **PRD Item #2 (ComplianceGuard dynamic regional gating)**.
* See [v1.4.0 PRD Draft (R1D10/R1D11)](PRD_DRAFT.md) for the technical specs on injecting localized crisis response cards (e.g., 988, 112, 13 11 14).
