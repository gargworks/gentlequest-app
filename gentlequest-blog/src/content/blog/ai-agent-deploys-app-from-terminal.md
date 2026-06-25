---
title: "My AI Agent Deploys My App to Both Stores From Terminal"
description: "No Xcode. No Play Console. No manual uploads. Two commands ship production updates to App Store and Google Play. Here's the exact setup."
pubDate: 2026-06-25
author: "Lokesh Garg"
tags: ["AI Agents", "Flutter", "Deployment", "Automation", "DevOps"]
---

I haven't opened Xcode in three weeks.

I haven't logged into Google Play Console in a month. My last
three app updates — bug fixes, a compliance gate fix, a chat screen
redesign — all shipped to both stores from my terminal. Two commands.
No clicks. No drag-and-drop. No web UI.

An AI agent did it.

Not "AI-assisted." Not "AI wrote the code and I deployed."
The agent read a deployment file, built the app, signed it,
uploaded the IPA to App Store Connect, uploaded the AAB to
Google Play, committed the version bump, and pushed to git.
I watched it happen in my terminal. That's it.

## The setup

The whole thing is one markdown file. That's the part that
surprised me — I expected to need a CI/CD pipeline, a Fastlane
configuration, a Makefile, maybe a Docker container. Instead,
it's a single document that any AI agent can read and execute.

Here's what's in it:

### Credentials (stored on disk, referenced by path)

```
App Store Connect:
  API Key:     ~/.appstoreconnect/private_keys/AuthKey_XXXX.p8
  Issuer ID:   ~/.appstoreconnect/issuer_id.txt
  API Key ID:  XXXX
  Team ID:     XXXXXXXXXX

Google Play:
  Service Account JSON:  ~/Downloads/project-sa.json
  Package Name:          com.yourapp.id
```

The agent doesn't need these explained. It reads the file,
finds the paths, and uses them.

### Build commands

```bash
# Android AAB
flutter build appbundle --release

# iOS IPA (codesigned, App Store ready)
flutter build ipa --release
```

### Upload commands

```bash
# iOS → App Store Connect
xcrun altool --upload-app -t ios \
  -f build/ios/ipa/yourapp.ipa \
  --apiKey XXXX \
  --apiIssuer your-issuer-id

# Android → Google Play
fastlane supply \
  --aab build/app/outputs/bundle/release/app-release.aab \
  --package_name com.yourapp.id \
  --track production \
  --json_key ~/Downloads/project-sa.json \
  --release_status completed \
  --skip_upload_metadata --skip_upload_images --skip_upload_screenshots
```

That's it. That's the entire deployment pipeline.

## Why this works

The key insight is that `xcrun altool` and `fastlane supply`
are already command-line tools. They don't need a web UI.
The reason we all use Xcode and Play Console is that
remembering the CLI flags and credential paths is annoying.

But an AI agent doesn't find it annoying. It reads a file,
fills in the variables, and runs the command. The friction
that makes web UIs valuable for humans is zero friction
for an agent.

## The full release flow

When I want to ship an update, I tell my agent:

> "Ship version 1.4.2 with the chat screen fix to both stores."

The agent:

1. Bumps the version in `pubspec.yaml`
2. Runs `flutter build appbundle --release`
3. Runs `flutter build ipa --release`
4. Runs `xcrun altool` to upload the IPA
5. Runs `fastlane supply` to upload the AAB
6. Commits the version bump
7. Pushes to git

Total time: about 15 minutes (most of it is Flutter compiling).
My involvement: one sentence.

## What about errors?

The deployment file includes a common errors table:

| Error | Fix |
|-------|-----|
| Version code already used | Bump build number, rebuild |
| Bundle version must be higher | Bump build number, rebuild |
| No signing certificate | Rebuild without `--no-codesign` |

When the agent hits an error, it reads the table, applies the fix,
and retries. I've watched it recover from a "version code already
used" error by bumping the build number and re-uploading — without
asking me.

## What about the blog?

The blog you're reading this on? Also deployed by the same agent.
It's an Astro static site on Render. The agent runs:

```bash
git add gentlequest-blog/
git commit -m "blog: new post"
git push origin main
```

Render auto-deploys on push. No manual deploy step.

## Is this safe?

The credentials never leave your machine. The agent reads files
that are already on disk. No secrets are sent to any API. The
upload commands use Apple's and Google's official CLI tools —
the same tools a CI/CD pipeline would use.

The difference is: instead of putting your secrets in GitHub
Actions or a CI environment, they stay on your machine and
the agent uses them locally.

## The one file that makes it work

The entire setup lives in a single file in my repo:
`docs/STORE_DEPLOYMENT.md`. Any AI agent — Devin, Claude Code,
Cursor, Windsurf — can read it and deploy.

The file has:
- Credential paths (not the secrets themselves)
- Build commands
- Upload commands
- Version bump protocol
- Error recovery table
- Full copy-paste release flow

I also added a pointer in `AGENTS.md` so any new agent knows
to read the deployment file first:

```markdown
## 0. Store Deployment (Read First)

All store deployment credentials and commands live in one place:
→ docs/STORE_DEPLOYMENT.md

Any agent deploying to stores should read that file first.
Do not search for credentials across the filesystem.
```

## What this actually means

I'm not going to pretend this is revolutionary. Fastlane exists.
xcrun altool exists. CI/CD pipelines exist. What's new is the
ergonomics:

- No CI/CD infrastructure to maintain
- No GitHub Actions billing
- No secrets in a third-party environment
- Any AI agent can do it by reading one file
- It runs on your laptop, not a build server

The deployment pipeline went from "open Xcode, archive, wait,
open Transporter, drag IPA, wait, open Play Console, create
release, upload AAB, wait" to "tell my agent to ship it."

That's not a product. That's just a better way to work.

---

*If you want the exact template to set this up for your own
Flutter app, I packaged it as a downloadable kit with setup
instructions: [Flutter Store Deployment Kit](https://lokeshgarg.gumroad.com/l/flutter-deploy)*

*This post was deployed by the same AI agent that ships my app
updates. It committed this file, pushed to git, and Render
published it. I wrote the words. The agent did the rest.*
