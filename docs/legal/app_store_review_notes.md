# App Store Review Notes — GentleQuest v1.3.0

**Prepared for:** App Store Connect submission (Apple review team)
**Date:** 2026-05-14
**Build:** v1.3.0

---

## Demo account

No demo account required. GentleQuest does not require sign-in to use. The full experience — chat, mood logging, journal, assessments — is available with an anonymous session ID generated on first launch.

---

## What's new in v1.3.0

v1.3.0 ships the R1 redesign: 21 screens redesigned around warmth-over-utility, skip-anything-no-shame UX, and the hard rule that crisis resources are never blocked. Release notes: `app_store_assets/v1.3.0/metadata.md`.

---

## Mental health app compliance disclosure

**Category:** Wellness companion — not a medical device, not therapy, not diagnosis.

**Disclaimers (where the user sees them):**
1. **First launch / onboarding:** Safety & Legal acknowledgment sheet shown before the user reaches any content screen. Includes "not medical advice" notice, crisis hotline callout (988), and links to full Terms and Privacy Policy. Requires explicit "I understand" tap.
2. **Settings → About → Crisis resources:** Shows Safety & Legal sheet at any time, no navigation required.
3. **In-chat crisis card:** When crisis-keyword detection triggers, an inline card with 988 deeplink appears before Alex's next response.
4. **PHQ-9 / GAD-7 results screen:** Shows "These are not a diagnosis" disclaimer with link to professional help.

**P6 — Crisis never blocks:** The app's hard product rule is that crisis resources are reachable from every screen, including blocked-region and offline states. The 988 banner is persistent when a crisis card is active.

---

## Privacy nutrition labels

See `docs/legal/privacy_policy.md` § "Apple App Privacy Nutrition Labels" for the full matrix. Summary:

| Category | Collected | Linked to User |
|---|---|---|
| Health & Fitness (mood, PHQ-9/GAD-7) | Yes | No |
| User Content (journal, chat) | Yes | No |
| Diagnostics (crash logs) | Yes | No |
| Identifiers (anonymous session UUID) | Yes | No |
| Location (coarse — state/country) | Yes | No |
| Usage Data (analytics events) | Yes | No |
| Contact Info (email — optional) | Yes | Yes (if provided) |

All other categories: NOT COLLECTED. No cross-app tracking. No data broker sharing.

---

## Regional restriction (IL / UT / WA)

The app actively restricts users in Illinois, Utah, and Washington (state-specific AI mental health regulations under evaluation). Restricted-region detection uses coarse location (IP geolocation or device locale). The blocked-region screen:
- Surfaces local crisis resources (988, Crisis Text Line, state hotline)
- Does not accept or store any user input
- Includes a "Learn more" link explaining the restriction

---

## Reviewer testing path

1. **Launch** → cycle through onboarding (3 trust chips + age gate at 18+)
2. Tap **Talk** tab → notice Alex's gentle greeting + chip starter set (chips populate the input, no auto-send)
3. **Mood** tab → log a mood with optional context chips (1–5 scale)
4. Tap **profile icon** (top-right) → Journal / Safety Plan / Library / Resources accessible
5. **Settings → Your Data → Anonymity mode** → toggle on → notice ANONYMOUS pill in nav + grayed notifications section
6. **Settings → Your Data → Export my data** → returns a JSON bundle inline (no email required)
7. **Crisis path test:** in the Talk tab, send "I want to hurt myself" → inline crisis card appears with 988 deeplink. Alex responds with a warm de-escalation, not a generic bot response.
8. **Regional restriction test:** set device region to Illinois → app shows blocked-region screen with crisis resources; no chat/mood UI is accessible.

---

## Privacy policy URL

The public privacy policy is hosted at: **https://gentlequest.app/privacy**

The in-app privacy policy viewer renders `assets/legal/privacy.md` (bundled in the app binary) so it works offline. The hosted URL is what Apple cross-checks against App Store Connect Privacy Nutrition Labels.

**Operator action required:** Ensure `https://gentlequest.app/privacy` is live and returns the content from `docs/legal/privacy_policy.md` before submitting to review. Mismatch between hosted URL content and the nutrition label answers is a common rejection trigger.

---

## Terms / EULA URL

The public EULA/Terms are hosted at: **https://gentlequest.app/terms**

The in-app Terms viewer renders `assets/legal/terms.md` (bundled).

**Operator action required:** Ensure `https://gentlequest.app/terms` is live before submitting.

---

## Operator action checklist (before hitting "Submit for Review")

- [ ] Host `https://gentlequest.app/privacy` with content matching `docs/legal/privacy_policy.md`
- [ ] Host `https://gentlequest.app/terms` with content matching `docs/legal/eula.md`
- [ ] Submit App Privacy nutrition labels in App Store Connect matching the matrix in `docs/legal/privacy_policy.md` § "Apple App Privacy Nutrition Labels" (manual step — cannot be scripted)
- [ ] Legal counsel review of `docs/legal/privacy_policy.md` and `docs/legal/eula.md` — these are operator-drafted, not reviewed by a lawyer
- [ ] Confirm university counselor alert path (CounselorAlert model) is **disabled** in the consumer App Store build — this path should only be active in enterprise/university deployments. If it is active, the privacy policy needs an update to the "University counselor alert path" section.
- [ ] Confirm `CrisisEvent.message` field behavior — the `models.py` schema stores the message content alongside the crisis flag. Verify this is disclosed accurately in the privacy policy "Crisis data" section, or suppress message content storage in the consumer build.
- [ ] Translation to other languages (out of scope for v1.3.0, flag for v1.4.0)
