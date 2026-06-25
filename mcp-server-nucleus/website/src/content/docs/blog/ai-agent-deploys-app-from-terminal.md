---
title: "AI Agents Can Ship to Production: A Deployment Case Study"
description: "How a single markdown file let an AI agent deploy a Flutter app to App Store and Google Play from terminal — no Xcode, no Play Console, no CI/CD pipeline."
date: 2026-06-25
author: "Eidetic Works"
tags: ["AI Agents", "Deployment", "Automation", "Case Study"]
---

I haven't opened Xcode in three weeks.

My AI agent deploys my app to both App Store and Google Play from
terminal. Two commands. No web UI. No drag-and-drop. No CI/CD
pipeline. The agent reads a deployment file, builds the app,
signs it, uploads to both stores, commits the version bump,
and pushes to git.

This is a case study in what AI agents can do when you give
them readable instructions and local access to tools that
already exist.

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

The file includes the exact `xcrun altool` command for App Store
Connect and the exact `fastlane supply` command for Google Play —
with all flags, credential paths, and track configuration filled in.

I'm not going to paste them here because they're the core of what
makes the kit worth paying for. But the shape is simple: one CLI
command per store, using credentials already on disk.

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

This is the pattern that makes agent-readable infrastructure
powerful: you don't need to build new tools for agents. You
need to make existing tools readable.

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

This is where agent-readable instructions beat scripts: the agent
can reason about errors and apply fixes contextually. A script
fails. An agent adapts.

## Is this safe?

The credentials never leave your machine. The agent reads files
that are already on disk. No secrets are sent to any API. The
upload commands use Apple's and Google's official CLI tools —
the same tools a CI/CD pipeline would use.

The difference is: instead of putting your secrets in GitHub
Actions or a CI environment, they stay on your machine and
the agent uses them locally.

This is the local-first principle applied to deployment: your
secrets, your machine, your agent.

## The pattern: agent-readable infrastructure

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

The pointer file is a few lines — I include the exact template
in the kit so you can drop it into your repo as-is.

This pattern — a single readable file that any agent can
execute — works for more than just deployment. It works for
any repeatable workflow:

- Database migrations
- Server provisioning
- Incident response
- Content publishing
- Data pipelines

If a human can do it by following instructions, an agent can
do it by reading them.

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

That's not a product. That's a better way to work. And it's
a glimpse of what agent-readable infrastructure makes possible.

---

*This post was deployed by the same AI agent that ships my app
updates. It committed this file, pushed to git, and the site
auto-published. I wrote the words. The agent did the rest.*

*If you want the exact template to set this up for your own
app, I packaged it as a downloadable kit:
[Flutter Store Deployment Kit](https://eideticworks.gumroad.com/l/flutter-deploy)*
