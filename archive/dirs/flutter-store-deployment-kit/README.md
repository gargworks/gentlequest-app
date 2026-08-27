# Flutter Store Deployment Kit

> Ship your Flutter app to App Store + Google Play from terminal with AI agents.
> No Xcode. No Play Console. No CI/CD pipeline. Two commands.

## What is this?

A set of templates that let any AI agent (Devin, Claude Code, Cursor, Windsurf)
deploy your Flutter app to both stores by reading a single markdown file.

Instead of opening Xcode, archiving, opening Transporter, dragging the IPA,
opening Play Console, creating a release, and uploading the AAB — you tell
your AI agent "ship version 1.0.1 to both stores" and it does the rest.

## What's included

| File | Purpose |
|------|---------|
| `STORE_DEPLOYMENT.md` | Single source of truth — credentials, commands, error recovery |
| `SETUP.md` | 15-minute setup guide |
| `AGENTS.md.template` | Pointer file so agents know where to look |

## How it works

1. You store credentials on your machine (API keys, service account JSON)
2. `STORE_DEPLOYMENT.md` references those paths + has all build/upload commands
3. Your AI agent reads the file and executes the full deploy flow
4. No secrets leave your machine — the agent uses official CLI tools locally

## Requirements

- Flutter SDK
- Xcode (macOS, for iOS builds)
- `fastlane` (`brew install fastlane`)
- App Store Connect API key
- Google Play service account JSON

## License

Personal use license. One purchase per developer/team.

---

*Made by Eidetic Works — building AI agents that ship real things.*
