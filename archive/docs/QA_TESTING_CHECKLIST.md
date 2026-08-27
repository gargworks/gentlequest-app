# GentleQuest — AI Testing Checklist & Expectations

> Created 2026-08-12 for cross-device QA testing of Stage 1 features.
> Run through this checklist on each device (Chrome, iPhone, Android).

## Test Environment
- **App:** Flutter debug build with `--dart-define=DEV_BYPASS_COMPLIANCE=true`
- **Backend:** https://gentlequest.onrender.com (production)
- **Devices to test:** Chrome (desktop), Chrome (mobile viewport), iPhone, Android

---

## 1. Onboarding Flow (Redesigned)

### Expectations
- [ ] Splash screen appears briefly (< 2s on web)
- [ ] Welcome screen shows: hero, headline, trust chips, CTA button
- [ ] Inline safety/legal disclosure visible at bottom of welcome (small text, not a popup)
- [ ] "Terms" and "Privacy Policy" are tappable links
- [ ] Age confirmation works (tapping CTA shows age modal)
- [ ] NO Safety & Legal popup after entering chat
- [ ] NO Web-to-phone promo popup (should be a non-blocking banner instead)
- [ ] Straight to chat after welcome + compliance

### Friction to watch for
- Any modal/popup that blocks before chat = FAIL
- Inline disclosure not visible = FAIL
- Links not opening = FAIL

---

## 2. Companion Creature (New — Stage 1 Core)

### Expectations
- [ ] Companion creature (🌱 seed) visible in chat header
- [ ] Tapping companion shows an encouraging SnackBar message
- [ ] Message is never shaming or punishing (no "you missed X days")
- [ ] Logging a mood triggers companion XP gain (+5 XP per check-in)
- [ ] Companion grows through stages at XP thresholds:
  - 🌱 Seed (0 XP)
  - 🌿 Sprout (50 XP)
  - 🌳 Sapling (150 XP)
  - 🦊 Young (400 XP)
  - 🦉 Mature (1000 XP)
- [ ] Growth progress bar visible below companion
- [ ] Total active days shown (NOT streak — anti-streak design)
- [ ] Level-up animation plays when crossing stage threshold
- [ ] Companion XP never decrements (absence never punished)

### Friction to watch for
- Companion not visible = FAIL
- Tap shows no message = FAIL
- Mood check-in doesn't add XP = FAIL
- Streak language anywhere = FAIL
- XP decreasing = FAIL

### How to test XP growth quickly
- Log 10 moods rapidly → should reach 50 XP → 🌱 becomes 🌿
- Check progress bar updates
- Check level number increases

---

## 3. Shareable Mood Card (New — Stage 1)

### Expectations
- [ ] Weekly review screen accessible (mood tab → weekly review)
- [ ] "Share your week" button visible after weekly review
- [ ] Tapping button opens bottom sheet with mood card
- [ ] Card shows: mood emoji, week label, mood shape (7-day bar chart)
- [ ] Card shows GQ branding/footer with logo
- [ ] Card shows encouraging message based on week's data
- [ ] "Share" button captures card as PNG and opens share sheet
- [ ] Shared text includes UTM-tagged deep link (ref=shared_card)
- [ ] Card uses LIVE week data (not stub/hardcoded)

### Friction to watch for
- Button not visible = FAIL
- Card shows "Week of Mar 18-24" (stub) = FAIL (live data not wired)
- Share button doesn't capture PNG = FAIL
- No UTM link in shared text = FAIL

---

## 4. Mobile UX (Landing Page + Blog)

### Landing Page (gentlequest.app)
- [ ] Hamburger nav button visible on mobile (≤640px viewport)
- [ ] Hamburger button is at least 44x44px touch target
- [ ] Tapping hamburger opens dropdown nav with all links
- [ ] Nav links: Features, 988, Blog, About, Get the app, Open app
- [ ] Tapping a nav link closes the dropdown
- [ ] "Or check in on the web" CTA has adequate touch target (≥44px height)
- [ ] Page renders without horizontal scroll on 375px viewport
- [ ] Google Fonts preconnect present (check network tab for fonts.gstatic.com)

### Blog (gentlequest.app/blog/)
- [ ] Blog index page loads (was 404 before)
- [ ] All 12+ posts listed with title, date, description
- [ ] Blog post URLs serve actual article content (not homepage)
- [ ] Mid-article CTA visible within blog posts
- [ ] Secondary store buttons (iOS/Android) have ≥44px touch target
- [ ] Share buttons have ≥44px touch target and ≥8px spacing
- [ ] Blog header nav visible on mobile (inline, not hidden)

### www redirect
- [ ] www.gentlequest.app → 301 redirect → gentlequest.app
- [ ] No canonical conflict in Search Console

---

## 5. Sitemap & SEO

- [ ] https://gentlequest.app/sitemap-index.xml serves XML (content-type: application/xml)
- [ ] https://gentlequest.app/sitemap-0.xml serves XML with all 35 URLs
- [ ] Sitemap submitted to Google Search Console (0 errors)
- [ ] Blog posts starting to appear in Google index (check in 1-2 weeks)

---

## 6. Funnel & Analytics

### Funnel API (gentlequest.onrender.com/api/metrics/funnel)
- [ ] landing_sessions > 0
- [ ] cta_clicks > 0 (once CTA beacon fix is deployed)
- [ ] web_app_opens > 0 (once CTA beacon fix is deployed)
- [ ] first_value_actions > 0
- [ ] cta_ctr > 0

### Funnel History (gentlequest.onrender.com/api/metrics/funnel/history)
- [ ] count > 0 (once scheduler fix is deployed)
- [ ] Snapshots appearing daily at 08:00 UTC

### GA4
- [ ] Sessions recorded
- [ ] Device breakdown shows both desktop and mobile
- [ ] Blog pages appearing in top pages
- [ ] Non-direct traffic > 0 (once Google indexes blog)

### Search Console
- [ ] Impressions > 0 (once Google indexes blog posts)
- [ ] Clicks > 0 (once blog posts rank for search terms)
- [ ] Indexed pages > 6 (currently 6, should grow to 35+)

---

## 7. D14 Retention Pipeline

### Expectations
- [ ] `metrics/d14_cohort.sql` exists and is parameterized
- [ ] `metrics/d14_cohort_read.py --start 2026-07-01` runs against production DB
- [ ] Output shows: cohort_date, cohort_size, d14_returned, d14_rate, verdict
- [ ] INSUFFICIENT verdict when cohort_size < 40
- [ ] PASS verdict when d14_rate ≥ 0.20
- [ ] FAIL verdict when d14_rate < 0.20

### Cannot test until
- DATABASE_URL is available (Render env var)
- Enough users exist for n≥40 cohort

---

## 8. Web Mobile Banner (New — replacing popup)

### Expectations
- [ ] Non-blocking banner appears at top of chat on web only
- [ ] Shows "GentleQuest is also available as a mobile app"
- [ ] "Get the app" link present
- [ ] Dismiss (X) button works
- [ ] Banner does not reappear after dismissal
- [ ] Banner does NOT appear on mobile (kIsWeb check)
- [ ] Chat is fully usable while banner is visible

---

## Device-Specific Notes

### Chrome (Desktop)
- Window size: 1280x800 default
- Test hamburger nav by resizing to ≤640px
- Shareable card: check PNG capture works in browser

### Chrome (Mobile viewport)
- Use DevTools mobile emulation (375x812 iPhone 12 Pro)
- Test touch targets are ≥44px
- Test no horizontal scroll

### iPhone
- Need Developer Mode enabled + valid provisioning profile
- Test haptic feedback on mood selection
- Test share sheet integration (native iOS share)

### Android
- Test share sheet integration (native Android share)
- Test Play Age Signals API (if applicable)

---

## Test Execution Log

| Date | Device | Tester | Results | Notes |
|------|--------|--------|---------|-------|
| 2026-08-12 | Chrome | Claude (automated) | 45 unit tests pass | Companion + shareable card |
| | Chrome | Lokesh | Companion visible, tap works | Visual QA partial |
| | iPhone | — | Blocked | Developer Mode + provisioning profile issue |

---

## Known Issues (Not Blockers)

1. **1px RenderFlex overflow** in shareable_mood_card.dart `_MiniBarSlot` (SizedBox(56) too small at default text scale) — cosmetic, doesn't crash
2. **3 pre-existing `use_build_context_synchronously` info warnings** in interactive_chat_screen.dart and mood_tracker.dart — not from new code
3. **Flutter web doesn't render in headless Chromium** — known Playwright limitation, needs real browser
4. **iOS provisioning profile expired** — needs Xcode signing refresh
5. **Flask fixes undeployed** — blocked on GitHub auth (CTA beacon + funnel scheduler)
