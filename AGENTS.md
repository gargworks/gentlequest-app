# AGENTS.md

## 0. STORE DEPLOYMENT (Read First)

**All store deployment credentials and commands live in one place:**
→ [`docs/STORE_DEPLOYMENT.md`](docs/STORE_DEPLOYMENT.md)

This file contains:
- App Store Connect API key path, issuer ID, team ID
- Google Play service account JSON path, package name
- Build commands (AAB + IPA)
- Upload commands (`xcrun altool` + `fastlane supply`)
- Version bump protocol
- Full copy-paste release flow

**Any agent deploying to stores should read that file first.**
Do not search for credentials across the filesystem — they are already documented there.

## Operating Principles

**All agents must read and follow:** `~/.eidetic/OPERATING_PRINCIPLES.md`

1. Take ownership end-to-end — own the full task, don't stop at obstacles
2. Be proactive — fix/flag discovered issues, follow up on open threads
3. Don't ask permission on obvious next steps — act on clear paths
4. Persist everything — keychain, resolver vault, growth engine, AGENTS.md
5. Verify before claiming done — test, check, confirm, read back
6. Track open threads — surface pending items, follow up on missed deadlines
7. Move fast, stay honest — bias toward action, never claim unverified success

---

An earlier multi-agent operating-org design (the "Nuclear Engine Operational Constitution" — agent roster, sprint mechanics, a 72-hour maintenance cycle) lived in this file. Its tooling (`agent_manager.py`, the codename roster, the sprint scripts) was never built, so it has been moved out of this live entry-point doc — see [`archive/docs/aspirations/AGENTS_nuclear_engine.md`](archive/docs/aspirations/AGENTS_nuclear_engine.md).
