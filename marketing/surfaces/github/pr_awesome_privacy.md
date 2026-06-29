# PR Draft — awesome-privacy

**Target Repo:** awesome-privacy (https://github.com/pluja/awesome-privacy)
**PR Title:** Add GentleQuest — local-first, privacy-preserving journaling & mood tracking

## PR Body

### What is being added?

GentleQuest — proposed for inclusion under the "Health" or "Notes & Journaling" category.

### Entry to add

```markdown
- [GentleQuest](https://gentlequest.app) - Local-first journaling and mood tracking. Encrypted on-device storage, no account, no cloud, no analytics. ([iOS](https://apps.apple.com/app/gentlequest/id6756537464) / [Android](https://play.google.com/store/apps/details?id=com.gentlequest.app) / [Web](https://gentlequest.app))
```

### Description

GentleQuest is a journaling and mood-tracking app that treats privacy as a foundational requirement, not a feature.

**Privacy architecture:**
- **Local-first:** All entries stored on the user's device. No server required for any core functionality.
- **Encrypted at rest:** Data is encrypted on-device. Physical access to the device does not grant access to entries.
- **No account:** No email, no login, no personal information required.
- **No cloud sync by default:** Sync is opt-in and end-to-end encrypted. The default is entirely local.
- **No analytics or tracking:** No telemetry, no usage data, no crash reporting that sends data to servers.
- **No third-party SDKs:** No ad SDKs, no social SDKs, no analytics SDKs that could exfiltrate data.
- **Offline by default:** Full functionality without internet connection.
- **Data export:** Users can export all data in standard formats at any time. No lock-in.

### Why it fits this list

awesome-privacy curates alternatives to privacy-invasive software. GentleQuest is a direct alternative to cloud-based journaling and mood-tracking apps that:

- Store sensitive personal reflections on company servers
- Require accounts that link entries to identity
- Include analytics SDKs that track user behavior
- Use journal content for AI training or product improvement
- Lock users into proprietary ecosystems with no export

In the mental health space, privacy is not a preference — it's a precondition for honest use. People self-censor when they know their thoughts are on a server. Local-first architecture removes that barrier.

### Links

- iOS: https://apps.apple.com/app/gentlequest/id6756537464
- Android: https://play.google.com/store/apps/details?id=com.gentlequest.app
- Web: https://gentlequest.app

### License / Cost

Free. No subscription for core features.

### Why this should be merged

The journaling/mood tracking category is one of the most privacy-sensitive in the app ecosystem. Users record their most unfiltered thoughts, fears, and struggles. The dominant apps in this category are cloud-based and account-dependent. GentleQuest provides a privacy-first alternative that belongs on this list alongside other local-first tools.

*This is not a diagnosis. Please see a qualified professional for clinical concerns.*
