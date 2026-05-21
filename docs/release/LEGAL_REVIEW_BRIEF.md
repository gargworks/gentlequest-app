# Legal review brief — GentleQuest 13+ age gate + cross-device sync

For counsel ahead of public launch. Last updated 2026-05-21.

## What changed

We lowered the in-app age gate from a blanket "must be 18+" to a region-aware
floor that matches the local legal minimum digital-consent age:

| Region | Minimum we serve |
|---|---|
| United States | 13 (COPPA cutoff for digital-service consent without parental flow) |
| United Kingdom | 13 (ICO digital age of consent) |
| EU member states defaulting to GDPR-K Article 8 floor | 13 |
| EU member states electing higher digital-consent age — Germany, France, Italy, Netherlands, Ireland, Luxembourg, Hungary, Lithuania, Poland, Romania, Slovakia, Cyprus, Croatia, Greece | 16 |
| Australia, Canada, New Zealand | 13 |
| India | 18 (Digital Personal Data Protection Act 2023 § 9) |
| Anywhere else (or region unknown) | 13 (universal floor, defensible default) |

The lookup table lives in `ai_buddy_web/lib/services/compliance_service.dart`,
function `ComplianceService.minAgeForRegion(region)`.

Region is detected via server-IP geolocation at first launch
(`/api/compliance/ip-region-check`) and stored on the device's session
record. The compliance-blocked-region list (Illinois WOPR / Utah HB452 /
Washington MHMDA) gates *independently* of age.

## What we collect from a user who's under-18-but-above-region-minimum

The same data we collect from any other user — chat messages, mood entries,
journal entries, assessment results, anonymous session id, and (only after
explicit opt-in sign-in) email address. No real name, no device hardware id,
no birth date stored beyond the at-launch attestation. Privacy policy
section "Children" updated alongside this change. Data is stored under the
device's session id and (post-sign-in) bound to the user's account.

## Specific items to validate with you

1. **COPPA exposure (US)**. Are we comfortable serving 13-17 in the US
   under the standard COPPA carve-out (services for >12 + no behavioral
   advertising)? Our profile:
   - No behavioral ads
   - Email collected only on explicit opt-in (no email at sign-up)
   - No precise geolocation collected
   - Crisis-detection ML is server-side but not used for ads
2. **GDPR-K (EU)**. We auto-step the floor to 16 in the countries listed
   above. Are there other EU member states where we should also use 16?
   Are there any where 14 or 15 is the legal minimum but we should still
   serve at 13 if we frame the data processing as legitimate interest /
   contract performance rather than consent?
3. **DPDP 2023 (India)**. We currently gate India at 18+ because § 9
   appears to require verifiable parental consent for under-18 users and
   we don't have a parental-consent flow built. Confirm 18+ is the right
   floor; flag if the act provides a digital-service exemption we
   missed.
4. **State-level US laws** beyond Illinois/Utah/Washington (already
   blocked):
   - Colorado AI Act (effective June 2026) — does our AI companion
     trigger the deployer obligations under CO § 6-1-1701 et seq.?
   - California — we collect minor user data; do we need explicit CCPA
     "for sale of personal information of minors" attestations even
     though we don't sell data?
5. **App Store / Play Store age rating**. We've been rating 17+ on
   iOS / Mature 17+ on Play. With the 13+ gate, what rating should
   we self-attest? (We carry mental-health content + crisis resources;
   that may carry 12+ or 17+ depending on store policy.)
6. **Cross-device sync via passwordless email**. Specifically:
   - Magic-link tokens are 32-byte URL-safe random, stored as
     SHA-256(token) only, 15-minute TTL, single use. Acceptable for
     compliance with NIST 800-63B SP "out-of-band authenticator"
     guidance?
   - We don't store email-password pairs. Is the "passwordless email"
     pattern accepted by GDPR data-minimization principles?
   - On account deletion, we set `users.deleted_at` and null
     `email` + `session_id` (see `routes/auth.py` and the delete-
     account flow). Confirm this meets GDPR "right to erasure" + CCPA
     "right to delete" requirements.

## Where the code lives, for spot reading

- Age gate logic: `ai_buddy_web/lib/services/compliance_service.dart`
- Age modal copy: `ai_buddy_web/lib/screens/compliance_guard_screen.dart`
  + `ai_buddy_web/lib/screens/welcome_screen.dart`
- Magic-link auth: `routes/auth.py`
- AuthToken schema: `models.py:AuthToken`
- Cross-device session inheritance: `routes/auth.py:verify_magic_link`
- Privacy policy: `ai_buddy_web/assets/legal/privacy.md`

## Questions we want a written answer on

a. Can we serve 13-17 users in each named jurisdiction without a parental-
   consent flow?
b. If yes, are there processing-purpose qualifiers we have to declare
   (GDPR-K legitimate interest vs. consent)?
c. What's the App Store / Play Store age-rating implication?
d. Any disclosures we should add to the in-app age-gate copy beyond
   "We need to confirm you're 13 or older"?
e. Is the passwordless-email + SHA-256-hashed-token pattern adequate
   for the authentication assurance level we're claiming?

Once these have written answers we'll know whether to ship at 13+ at launch
or stage to 16+ initially and lower after a compliance review window.
