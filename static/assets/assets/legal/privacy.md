# GentleQuest Privacy Policy

**Effective date:** 2026-05-14
**App version:** 1.3.0
**Contact:** hi@eidetic.works

---

## Summary

GentleQuest is built to stay quiet. We collect the minimum we need to make the app work, and we give you tools to see, export, and delete everything.

---

## What we collect

### Always collected (to operate the service)

- **Anonymous session ID** — a UUID generated per device. Regenerable via Settings → Your Data → Reset Session. Not linked to your name, email, or device hardware ID.
- **Crash logs** — sent to Firebase Crashlytics. No PII; IP addresses are truncated to /24 (IPv4) or /48 (IPv6) before storage.
- **Region** — US state or country-level, used for compliance gating (blocked-region check) and to surface the right crisis line. We never store your precise location or street address.

### Collected only when you use those features

| Feature | What we store |
|---|---|
| Mood logging | Mood level (1–5 scale), optional free-text note, optional context chips you select, timestamp |
| Journal | Entry title (optional), body text, mood tag, created/updated timestamps |
| Chat with Alex | Full message content, is-user flag, risk level flag, message type, timestamp |
| Clinical assessments (PHQ-9 / GAD-7) | Integer responses per question, total score, severity label, timestamp. Never rendered as a diagnosis. |
| Notification preferences | Toggle states and reminder time — stored server-side only when you have an account session |
| Analytics events | Event type, anonymized metadata, timestamp — suppressed entirely when Anonymity Mode is on |

### NOT collected

- Real name or email address (email is optional and only requested during OAuth sign-in, which is not required)
- Device hardware identifiers (IDFA, IDFV, Android Advertising ID)
- Precise GPS location
- Contacts or address book
- Microphone audio (voice input, if available, is processed on-device only; audio is never uploaded)
- Camera roll or photo library
- HealthKit / Apple Health data (we do not request this entitlement)
- Browsing history outside the app

---

## Anonymity mode

Toggle in **Settings → Your Data → Anonymity mode**. When on:

- Firebase Analytics events are suppressed for your session
- IP addresses are not stored for new requests
- Device identifiers are not stored
- Your push notification token is released (notifications pause while on)

Anonymity mode does **not** delete data already stored — use **Settings → Delete Account** for that.

---

## Your data, your control

**View and export:** Settings → Your Data → Export my data. Returns a JSON bundle containing: mood entries, journal entries, chat history, self-assessments, and analytics events. Delivered inline (not emailed) at the time of request.

The export bundle mirrors what the `/api/user/export` endpoint returns:
- `profile` — email (if provided), created_at, anonymity_mode, notification_prefs
- `mood_entries` — mood_level, note, contextChips, timestamp
- `journal_entries` — id, title, body, moodTag, createdAt, updatedAt, deletedAt
- `chat_history` — content, is_user, timestamp, risk_level, message_type
- `self_assessments` — timestamp, assessment_data
- `analytics_events` — event_type, metadata (IP/device fields stripped if anonymity_mode is on), timestamp

**Delete:** Settings → Delete Account → type "DELETE" to confirm. The server cascade-removes:
- Mood entries, journal entries, chat messages, conversation logs
- Clinical assessments, self-assessment entries
- Crisis events, crisis escalations
- Counselor alerts and alert acknowledgments
- Quest progress, user profile (XP/level/streak)
- Resource interactions
- Analytics events
- Push notification tokens / notification preferences
- The user record itself (email nulled, session_id nulled, deleted_at stamped)

Both actions apply within 30 days per GDPR Article 17 and CCPA § 1798.105.

---

## Crisis data

If you trigger a crisis path (tapping the 988 deeplink, crisis-keyword detection in chat, or PHQ-9 Q9 response ≥ 1):

- A `CrisisEvent` record is stored: session_id, risk_level, risk_score, keywords, timestamp, intervention_taken, escalated flag. **Message content is stored in the crisis_detections table alongside the flag.**
- A `CrisisEscalation` record may be stored: session_id, country_code, channel (sms/call/banner_only), timestamp.

**What we do NOT do:**
- We do not contact emergency services on your behalf.
- We do not share crisis data with third parties outside the university counselor alert path (see below).
- The 988 deeplink connects you directly to the Suicide and Crisis Lifeline. We are not party to that call or text.

**University counselor alert path (enterprise deployments only):**
If GentleQuest is deployed by a university and a high-severity crisis is detected, a `CounselorAlert` record may be sent to the university's designated counselor(s) — containing the severity level, the trigger message, a conversation excerpt, and risk keywords. This path is active only in university-configured deployments; it is **not active in the consumer App Store build**.

---

## AI processing

- Chat messages are sent to Google Gemini (primary) and/or OpenAI (fallback) for response generation.
- Messages are processed transiently for response generation only. We do not use your messages to train or fine-tune AI models.
- Crisis-keyword detection runs **on-device only** — the message is never sent to the cloud for this purpose.
- AI provider privacy policies: [gemini.google.com/privacy](https://gemini.google.com/privacy) · [openai.com/privacy](https://openai.com/privacy)

---

## Regional service restrictions

GentleQuest is currently **unavailable** in the following US states while we evaluate compliance with state-specific AI mental health regulations:

- **Illinois** (AIMHA — Artificial Intelligence Mental Health Act under evaluation)
- **Utah** (Utah AI Policy Act implications under evaluation)
- **Washington** (Washington State AI Act under evaluation)

Users in these states see a "Right now in [state]" screen with local crisis resources (988 + Crisis Text Line + state-specific lines). **No user input is stored when you are in a restricted region.**

---

## Children

GentleQuest is built for high-school-aged users and adults. The minimum age we serve depends on local law:

- **13+** in the United States (COPPA), United Kingdom (ICO digital age of consent), Australia, Canada, New Zealand, and most EU member states that have adopted the default GDPR-K Article 8 floor.
- **16+** in EU member states that elected a higher digital-consent age under GDPR-K (currently Germany, France, Italy, Netherlands, Ireland, Luxembourg, Hungary, Lithuania, Poland, Romania, Slovakia, Cyprus, Croatia, Greece).
- **18+** in India (Digital Personal Data Protection Act 2023) and any jurisdiction not listed above without a verified parental-consent flow.

We verify age at first launch and gate access to the regional minimum. Users under their region's minimum are offered a dignity path with external resources. We do not knowingly store any data from users below their region's minimum.

## Accounts and cross-device sync

Sign-in is optional. Anonymous use is fully supported and is the default.

When you choose to sign in:

- We collect your email address. It is used only to send the one-time passwordless sign-in link and to identify your account on future sign-ins.
- A 32-byte random token is sent in the sign-in link. The server stores only its SHA-256 hash; the raw token is never persisted. Tokens expire 15 minutes after issue and can be used once.
- After verification, your existing journal entries on this device are uploaded to the server so they're available when you sign in on another device.
- The data we store under your account is the same data we store under an anonymous session — chat messages, mood entries, journal entries, assessment results. Signing in does not unlock any new data category; it just lets you reach your data from multiple devices.
- When you sign out, the device returns to using a fresh anonymous session. Your server-side data stays bound to your email and can be reattached by signing back in.

---

## Compliance

| Regulation | Our approach |
|---|---|
| GDPR | Data subject rights (access, rectification, erasure, portability) supported via Export + Delete endpoints. Data processing basis: legitimate interest (service operation) + consent (optional features). |
| CCPA / CPRA | California residents: right to know, right to delete, right to opt-out of sale (we do not sell data). Exercise via Settings. |
| HIPAA | GentleQuest is **not** a HIPAA covered entity. We are not a healthcare provider, health plan, or healthcare clearinghouse. We do not provide medical care. |
| Illinois AIMHA / Utah / WA | Service blocked in these states pending compliance review. |

---

## Data retention

| Data type | Retention |
|---|---|
| Messages / conversation logs | Until account deletion (no automatic expiry beyond what deletion flow covers) |
| Mood entries, journal entries | Until account deletion |
| Clinical assessments | Until account deletion |
| Crisis events | Until account deletion |
| Analytics events | Until account deletion; suppressed during Anonymity Mode |
| Crash logs (Crashlytics) | 90 days (Firebase default) |
| Aggregated / anonymized analytics | Up to 90 days |

---

## Policy updates

We may update this policy for legal or product compliance. Material changes trigger an in-app notice on next launch. Historical versions are stored at `docs/legal/privacy_policy_history/`.

---

## Apple App Privacy Nutrition Labels

Use this matrix when filling in App Store Connect > App Privacy for GentleQuest v1.3.0.

| Category | Data Type | Collected | Linked to User | Used for Tracking |
|---|---|---|---|---|
| Health & Fitness | Mental health — mood entries, PHQ-9/GAD-7 scores | Yes | No (session ID only, no name/email required) | No |
| User Content | Journal entries, chat messages | Yes | No (session ID only) | No |
| Diagnostics | Crash logs, performance data (Crashlytics) | Yes | No | No |
| Identifiers | Anonymous session ID (UUID) | Yes | No | No |
| Location | Coarse — US state or country (for compliance gating) | Yes | No | No |
| Usage Data | App interaction events (suppressed in Anonymity Mode) | Yes | No | No |
| Contact Info | Email address | Yes — optional, only if user provides it | Yes — if provided | No |

**All other categories (Purchases, Financial Info, Browsing History, Sensitive Info, Other Data, Health, Fitness, Search History, Contacts, Photos/Videos, Audio, Gameplay Content):** NOT COLLECTED.

**Tracking:** GentleQuest does not track users across apps or websites owned by other companies, and does not share data with data brokers. Answer "No" to the App Store Connect tracking question.
