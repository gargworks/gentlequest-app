# 🎯 LOKESH STUDIO OPERATING SYSTEM
## The Definitive Manual for Multi-Project Development

> [!LOCK]
> **This is the single invocable reference.** Do **not delete or trim** any section without explicit human approval. Agents must ask the human before removing or altering any block tagged LOCK/CORE. Additions and append-only enhancements are welcome.

**Version:** 1.0.1  
**Created:** January 18, 2026  
**Author:** Claude Opus 4.5 (Thinking) + Antigravity + Windsurf  

> [!IMPORTANT]
> **Invoke this file first.** Treat this as the root context. If an agent needs more detail, follow the links here. No other upstream protocol supersedes this for experiments unless the human approves.

---

## 📖 Table of Contents

1. [Single Invocation & Locks](#single-invocation--locks)
2. [The Problem We Solved](#the-problem-we-solved)
3. [The Architecture](#the-architecture)
4. [Quick Start (30 seconds)](#quick-start-30-seconds)
5. [The Four Zones](#the-four-zones)
6. [Daily Workflow](#daily-workflow)
7. [The Scaffold Command](#the-scaffold-command)
8. [Rules of Engagement](#rules-of-engagement)
9. [Reusing Code & Patterns](#reusing-code--patterns)
10. [Graduating an Experiment](#graduating-an-experiment)
11. [Tool-Specific Notes](#tool-specific-notes)
12. [Troubleshooting](#troubleshooting)
13. [One-Page Cheatsheet](#one-page-cheatsheet)
14. [Asset Catalog (Pointer)](#asset-catalog-pointer)
15. [Useful Workflows](#useful-workflows)
16. [Available Protocols & Tools](#available-protocols--tools)
17. [Appendix A: Nucleus Assets & Templates](#appendix-a-nucleus-assets--templates-reference)

---

## Single Invocation & Locks

- **Invoke this file first** for any experiment or app work.
- **Locked sections**: Anything tagged LOCK/CORE here must not be deleted or edited without explicit human approval. Additive changes are fine.
- **Pointer discipline**: If more detail is needed, follow links from this file (CONTEXT_HUB.md, STUDIO_QUICKREF.md, scaffold script, aliases).
- **Workspace rule**: Experiments run as isolated workspaces. Do not multi-root with Mother Repo.

---

## The Problem We Solved

You had **scattered intelligence** across:
- `.agent/workflows/`
- `.brain/` (Nucleus artifacts)
- `.gemini/` (multiple locations)
- `AGENTS.md`, `PROTOCOL.md`
- Windsurf memories, Antigravity playgrounds
- 170+ scripts in `scripts/`

When you wanted to explore **new ideas** (not GentleQuest), you faced:
- **Context contamination**: tools assumed GentleQuest patterns
- **Accidental edits**: risk of breaking production code
- **Kernel sync drift**: any "shared kernel" would fall out of date
- **Frontloading**: you didn't know what you'd need upfront

**The solution**: a **pull-based, copy-on-need** system with explicit boundaries.

---

## The Architecture

```
/Users/lokeshgarg/
│
├── ai-mvp-backend/          ← MOTHER REPO (Production MVP)
│   ├── CONTEXT_HUB.md       ← The "Spine" (read this first)
│   ├── AGENTS.md            ← Personas & roles
│   ├── PROTOCOL.md          ← Rules of the house
│   ├── .agent/workflows/    ← Executable playbooks
│   ├── .brain/              ← Nucleus memory & artifacts
│   ├── providers/           ← Reusable AI patterns
│   ├── scripts/             ← Ops automation (GentleQuest-specific)
│   └── scripts/scaffold_experiment.sh  ← THE MAGIC COMMAND
│
├── experiments/             ← EXPLORATION ZONE (messy, fast)
│   ├── song-meaning/        ← Your first experiment
│   ├── whatsapp-revival/    ← Future experiment
│   └── ...
│
├── apps/                    ← SHIPPING ZONE (promoted, production-track)
│   └── (empty until you promote something)
│
└── archive/                 ← COLD STORAGE (legacy snapshots)
    └── (old WhatsApp repo, treasure hunt files, etc.)
```

**Key insight**: The Mother Repo stays canonical. Experiments get **copies** of governance docs at scaffold time. No symlinks. No cross-references. Clean isolation.

---

## Quick Start (30 seconds)

### To explore a new idea:

```bash
# From anywhere on your Mac:
cd ~/ai-mvp-backend
./scripts/scaffold_experiment.sh my-new-idea

# Then open the new workspace in your IDE:
# Antigravity/Windsurf/Cursor → Open Folder → ~/experiments/my-new-idea
```

### First thing to tell the agent in your new workspace:

> "Read CONTEXT.md and brief.md first."

That's it. You're now in a clean, isolated environment.

---

## The Four Zones

### 1. Mother Repo (`~/ai-mvp-backend/`)
- **What**: Production MVP (iOS/Android/Web + Nucleus MCP)
- **Rule**: Don't experiment here. This is sacred.
- **When to touch**: Only for GentleQuest/Nucleus work.

### 2. Experiments (`~/experiments/`)
- **What**: High-velocity prototypes, legacy revivals, messy exploration
- **Rule**: Break things freely. Nothing here is precious.
- **Lifecycle**: 1 day to 2 weeks. Kill or promote.

### 3. Apps (`~/apps/`)
- **What**: Promoted experiments ready for shipping
- **Rule**: Git init. CI/CD. Production mindset.
- **When to move here**: When you're ready to share with the world.

### 4. Archive (`~/archive/`)
- **What**: Cold storage for legacy snapshots
- **Rule**: Don't edit. Reference only.
- **Examples**: Old WhatsApp repo, college treasure hunt files.

---

## Daily Workflow

### Starting a new idea

```
1. Run scaffold     → ./scripts/scaffold_experiment.sh idea-name
2. Open workspace   → ~/experiments/idea-name
3. Tell agent       → "Read CONTEXT.md and brief.md"
4. Edit brief.md    → Define vision, success criteria, plan
5. Build in src/    → Write your code
6. Decide           → Kill, pivot, or promote
```

### Promoting an experiment to an app

```bash
mv ~/experiments/song-meaning ~/apps/song-meaning
cd ~/apps/song-meaning
git init
git add .
git commit -m "Initial commit: promoted from experiment"
```

### Archiving legacy code

```bash
# Just copy it in:
cp -r /path/to/old-repo ~/archive/old-repo-name-YYYY

# Never edit files in archive/
```

---

## The Scaffold Command

**Location**: `~/ai-mvp-backend/scripts/scaffold_experiment.sh`

**What it does**:
1. Creates `~/experiments/<name>/`
2. Creates subfolders: `src/`, `vendor/`, `docs/`
3. Copies governance docs: `AGENTS.md`, `PROTOCOL.md`, `CONTEXT_HUB.md`
4. Generates `CONTEXT.md` (experiment-local rules for agents)
5. Generates `brief.md` (your project plan template)

**What you get**:

```
~/experiments/my-new-idea/
├── CONTEXT.md        ← AGENT ENTRYPOINT (tells agent the boundaries)
├── brief.md          ← YOUR PLAN (edit this immediately)
├── AGENTS.md         ← Copied from Mother Repo
├── PROTOCOL.md       ← Copied from Mother Repo
├── CONTEXT_HUB.md    ← Copied from Mother Repo
├── src/              ← Your code goes here
├── vendor/           ← Vendored libraries (copy-on-need)
└── docs/             ← Documentation
```

**Safety features**:
- Won't overwrite existing experiments
- Uses relative paths (portable)
- Validates Mother Repo has required files

---

## Rules of Engagement

### For You (Human)

| DO | DON'T |
|----|-------|
| Run scaffold for every new idea | Create experiments inside ai-mvp-backend |
| Edit brief.md immediately | Leave placeholder text |
| Kill experiments that aren't working | Hoard dead experiments |
| Promote winners to ~/apps/ | Ship from ~/experiments/ |
| Archive legacy code untouched | Edit files in ~/archive/ |

### For Agents (Antigravity/Windsurf/Cursor)

The `CONTEXT.md` in each experiment tells agents:

1. **Do not modify** files outside the experiment directory
2. **Memory Isolation**: Do NOT write to the central brain (`~/ai-mvp-backend/.brain`) from here. Use local `./notes/` or `./docs/`.
3. **Refer to** local copies of AGENTS.md and PROTOCOL.md
4. **Ask for vendor/** if you need code from the main repo
5. **Never import** relative paths like `../../ai-mvp-backend`

---

## Reusing Code & Patterns

### The "Copy-on-Need" Strategy

When you need code from the Mother Repo:

```bash
# 1. Identify what you need
# Example: you want the Gemini provider pattern

# 2. Copy it into vendor/
cp ~/ai-mvp-backend/providers/gemini.py ~/experiments/my-idea/vendor/

# 3. Treat vendor/ as read-only reference
# Adapt the pattern, don't import it directly
```

### What's safe to copy

| Asset | Location in Mother Repo | Reusable? |
|-------|------------------------|-----------|
| Gemini patterns | `providers/gemini.py` | ✅ Yes (adapt) |
| Memory patterns | `providers/memory.py` | ✅ Yes (adapt) |
| Tool-use patterns | `providers/tools.py` | ✅ Yes (adapt) |
| Deploy scripts | `scripts/` | ⚠️ Mostly GentleQuest-specific |
| Crisis detection | `crisis_detection.py` | ⚠️ GentleQuest-specific |
| Workflows | `.agent/workflows/` | ✅ Yes (adapt) |

### What NOT to do

```bash
# ❌ DON'T symlink (agent can accidentally edit source)
ln -s ~/ai-mvp-backend/providers/gemini.py vendor/gemini.py

# ❌ DON'T import across repos
from ai-mvp-backend.providers import gemini  # WRONG

# ❌ DON'T open multi-root workspace with Mother Repo + experiment
# (increases accident risk)
```

---

## Graduating an Experiment

### When to promote (all must be true):
- [ ] MVP works
- [ ] You want to ship it publicly
- [ ] You're willing to maintain it

### How to promote:

```bash
# 1. Move to apps/
mv ~/experiments/song-meaning ~/apps/song-meaning

# 2. Initialize git
cd ~/apps/song-meaning
git init
git add .
git commit -m "Initial commit: Song Meaning AI"

# 3. Clean up
rm CONTEXT_HUB.md  # No longer needed (you're independent now)

# 4. (Optional) Push to GitHub
gh repo create song-meaning --private --source=. --push
```

### Post-promotion checklist:
- [ ] Add .gitignore
- [ ] Add README.md (real one, not template)
- [ ] Set up CI/CD if needed
- [ ] Remove governance docs you don't need

---

## Tool-Specific Notes

### Antigravity

- **Playground location**: `~/.gemini/antigravity/playground/`
- **Playground names**: Random (e.g., `lunar-lagoon`). Don't leave valuable work there.
- **Best practice**: Use Playground for <1hr throwaway work. Scaffold for anything longer.
- **Context loading**: Tell agent "Read CONTEXT.md first" when opening a new workspace.

### Windsurf

- **Global memories**: `~/.windsurf/` (tool-managed, don't edit manually)
- **Per-workspace**: Works normally with experiment folders
- **MCP**: Your Nucleus MCP works here too

### Cursor

- **Works the same**: Open experiment folder as workspace
- **Rules files**: You can add `.cursorrules` if needed

### All Tools

- Agents respect the `CONTEXT.md` directive if you remind them
- If an agent tries to edit outside the workspace, stop it and remind it of the rules
- Multi-root workspaces (Mother Repo + experiment) are risky—avoid

---

## Troubleshooting

### "Scaffold says directory already exists"

```bash
# Check if it exists
ls ~/experiments/

# Either remove it or pick a new name
rm -rf ~/experiments/old-experiment
# OR
./scripts/scaffold_experiment.sh my-idea-v2
```

### "Agent is trying to edit the Mother Repo from experiment"

1. Stop the agent
2. Remind it: "Read CONTEXT.md. You must not edit files outside this workspace."
3. If it persists, close the workspace and reopen only the experiment folder

### "I need a pattern from the main repo"

```bash
# Copy it to vendor/
cp ~/ai-mvp-backend/providers/something.py ~/experiments/my-idea/vendor/

# Then adapt it in src/
```

### "My experiment outgrew experiments/"

Promote it:
```bash
mv ~/experiments/my-idea ~/apps/my-idea
cd ~/apps/my-idea && git init
```

### "I want to update governance docs in an experiment"

Just edit them. They're copies. The Mother Repo is unaffected.

---

## One-Page Cheatsheet

```
┌─────────────────────────────────────────────────────────────────┐
│                 LOKESH STUDIO CHEATSHEET                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NEW IDEA:                                                      │
│    cd ~/ai-mvp-backend                                          │
│    ./scripts/scaffold_experiment.sh idea-name                   │
│    → Open ~/experiments/idea-name as workspace                  │
│    → Tell agent: "Read CONTEXT.md and brief.md"                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ZONES:                                                         │
│    ~/ai-mvp-backend/  → Production (don't experiment here)      │
│    ~/experiments/     → Exploration (break things freely)       │
│    ~/apps/            → Shipping (promoted experiments)         │
│    ~/archive/         → Cold storage (don't edit)               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  REUSE CODE:                                                    │
│    cp ~/ai-mvp-backend/providers/X.py ~/experiments/Y/vendor/   │
│    → Adapt in src/, don't import directly                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PROMOTE:                                                       │
│    mv ~/experiments/idea ~/apps/idea                            │
│    cd ~/apps/idea && git init                                   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GOLDEN RULES:                                                  │
│    ✓ Copy, don't symlink                                        │
│    ✓ Vendor code into vendor/, treat as read-only               │
│    ✓ Kill experiments that aren't working                       │
│    ✓ Tell agents "Read CONTEXT.md first"                        │
│    ✗ Never nest experiments inside Mother Repo                  │
│    ✗ Never edit files in ~/archive/                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

---

## Shell Aliases (Power-Up)

For even faster workflow, add shell aliases to your `~/.zshrc`:

```bash
# Add this line to ~/.zshrc
source ~/ai-mvp-backend/scripts/studio_aliases.sh
```

Then reload:
```bash
source ~/.zshrc
```

Now you can use:

| Command | Action |
|---------|--------|
| `exp-new idea` | Create new experiment |
| `exp-list` | List all experiments |
| `exp-open idea` | Open experiment in editor |
| `exp-promote idea` | Move to apps/ and git init |
| `exp-kill idea` | Delete experiment (with confirm) |
| `app-list` | List all apps |
| `app-open idea` | Open app in editor |
| `archive-add /path name` | Archive a folder |
| `archive-list` | List archived items |
| `studio` | cd to Mother Repo |
| `exps` | cd to experiments/ |
| `apps` | cd to apps/ |
| `studio-help` | Show full reference |

---

## Related Files

| File | Purpose |
|------|---------|
| `CONTEXT_HUB.md` | The "spine" - quick reference for agents |
| `STUDIO_MANUAL.md` | This file - full documentation |
| `STUDIO_QUICKREF.md` | Printable quick reference card |
| `scripts/scaffold_experiment.sh` | The main scaffold command |
| `scripts/studio_aliases.sh` | Shell aliases and functions |

---

## Final Words

This system is designed for **one person with many ideas**.

It gives you:
- **Speed**: 30-second setup for any new idea
- **Safety**: Production code is protected
- **Freedom**: Break experiments without fear
- **Clarity**: Always know where things belong

The Mother Repo (`ai-mvp-backend`) is your **source of truth** for patterns and governance. Experiments are **disposable explorations**. Apps are **committed bets**.

Now go build something.

---

*"The best system is one you actually use."*

— Lokesh Studio Operating System, v1.0.0

---

## Asset Catalog (Pointer)

- Core Studio assets: CONTEXT_HUB.md, STUDIO_QUICKREF.md, scaffold_experiment.sh, studio_aliases.sh, provider patterns (gemini/tools/memory)
- Truth-validation tools: anti-hallucination protocol, oracle prompts, gladiator_simulator (opt-in)
- Release templates: one_click_release.sh, release_android_apk.sh, release_ios_ipa.sh, complete_launch_checklist.sh
- For the full catalog (templates, playbooks, GTM, Nucleus assets, directories), see **Appendix A: Nucleus Assets & Templates**.

----

## Useful Workflows

### Truth Validation & Anti-Hallucination
- **Gladiator Simulator**: `python3 scripts/gladiator_simulator.py "Proposition" --save`
  - Tests strategic propositions against 31 mitigation strategies
  - Returns confidence score and strategy citation
  - Saves verdict to `.brain/memory/ORACLE_LEDGER.md`

### Brain & Nucleus Operations
- **Health Check**: `python3 scripts/nucleus_health_check.py`
  - Validates Nucleus MCP server and brain state
  - Checks event ledger, tasks, and commitments

- **Status Check**: Use `.agent/workflows/status.md`
  - See pending tasks and session identity
  - Register new sessions with `brain_register_session`

- **Session Management**: `python3 brain_save_session.py`
  - Saves current session context for resumption
  - Stores breadcrumbs and pending decisions

- **Task Queue**: `python3 scripts/brain_get_next_task.py`
  - Retrieves highest-priority unblocked task
  - Filters by required skills

### App Release & Deployment Templates
- **One-Click Release**: `./scripts/one_click_release.sh`
  - Complete release orchestration for iOS/Android
  - Runs launch checklist, builds, validates
  - Template for multi-platform app deployment

- **Android Release**: `./scripts/release_android_apk.sh` & `./scripts/release_android_aab.sh`
  - Automated APK/AAB builds with signing
  - Supports key.properties or env vars
  - Debug fallback for testing

- **iOS Release**: `./scripts/release_ios_ipa.sh`
  - Automated IPA builds with Xcode signing
  - Multiple export methods (app-store, ad-hoc)
  - Team ID and bundle ID configuration

- **Launch Checklist**: `./scripts/complete_launch_checklist.sh`
  - Pre-release validation (6,384 lines)
  - Checks build, signing, metadata, assets
  - Template for release readiness

> [!TIP]
> These scripts can be vendored into experiments as release templates. Adapt the signing and configuration sections for your app.

### Development & Deployment
- **Complete Test Suite**: `python3 scripts/run_all_tests.sh`
  - Runs all verification scripts in parallel
  - Generates comprehensive test report

- **Production Deploy**: `./scripts/deploy_production.sh`
  - Builds and deploys to Render
  - Includes health checks and rollback

- **Database Backup**: `./scripts/backup_database.sh`
  - Creates timestamped database backup
  - Stores in `.brain/backups/`

### Marketing & Outreach
- **Autopilot**: `python3 scripts/marketing_autopilot.py`
  - Runs automated marketing workflows
  - Generates content and tracks engagement

- **University Outreach**: `python3 scripts/generate_outreach.py`
  - Creates personalized university emails
  - Uses templates from `.brain/artifacts/gtm/`

> [!NOTE]
> All workflows are documented in `.agent/workflows/`. Use `status.md` for quick system overview.

---

## Available Protocols & Tools

> [!LOCK]
> The following are **available but not auto-enforced**. Use them when you explicitly need truth-validation or hallucination mitigation.

- `.brain/knowledge/ANTI_HALLUCINATION_PROTOCOL.md` (Maryam mitigation list) — **31 strategies** for hallucination mitigation. Use when you need rigorous truth-checking.
- `.brain/PROTOCOL_THE_ORACLE_v3.4.md` and Gladiator/Oracle prompts — **Strategic proposition testing**. Use for high-stakes decisions.
- `scripts/gladiator_simulator.py` — **Truth-audit runner**. Invoke with a proposition to get a confidence score and strategy citation.

> [!TIP]
> To run a truth audit: `python3 scripts/gladiator_simulator.py "Your proposition here" --save`

> [!NOTE]
> These tools are **opt-in**. They do not auto-run unless you explicitly invoke them.

---

## Appendix A: Nucleus Assets & Templates (Reference)

> [!NOTE]
> This appendix centralizes all reusable assets. Keep the main manual lean; browse here when you need templates or patterns.

### A1. Asset Classification & Usage Guide

#### 🟢 Direct Use (No Adaptation Needed)
| Asset | Path | Use Case |
|-------|------|---------|
| **Email Templates** | `.brain/artifacts/planning/EMAIL_LIBRARY_TEMPLATES_20260117.md` | 50+ copy-paste templates for outreach |
| **Project Context Template** | `docs/templates/PROJECT_CONTEXT_TEMPLATE.md` | LLM conversation context preservation |
| **Design Journal Template** | `docs/templates/DESIGN_JOURNAL_TEMPLATE.md` | Structured design documentation |
| **University Customization** | `docs/UNIVERSITY_CUSTOMIZATION_TEMPLATES.md` | University-specific configurations |
| **Beta Testing Templates** | `docs/BETA_TESTING_TEMPLATES.md` | Testing workflow templates |
| **Environment Examples** | `env.example`, `env.production.example` | Environment configuration templates |
| **Signing Examples** | `scripts/*_signing.env.example` | Code signing configuration |
| **Key Properties** | `ai_buddy_web/android/key.properties.example` | Android signing setup |
| **iOS Config** | `ai_buddy_web/ios/Config/*.example` | iOS bundle configuration |
| **Schemas** | `docs/schemas/*.json` | Data structure definitions |
| **MCP Config Example** | `mcp-server-nucleus/examples/claude_desktop_config.example.json` | MCP server setup |

#### 🟡 Adaptation Required (Modify for Your Use)
| Asset | Path | What to Adapt |
|-------|------|---------------|
| **One-Click Release** | `scripts/one_click_release.sh` | Change app name, paths, signing |
| **Android Release Scripts** | `scripts/release_android_*.sh` | Update package name, signing config |
| **iOS Release Script** | `scripts/release_ios_ipa.sh` | Change bundle ID, team ID, provisioning |
| **Launch Checklist** | `scripts/complete_launch_checklist.sh` | Adapt validation rules for your app |
| **Deploy Scripts** | `scripts/deploy_*.sh` | Update service names, URLs |
| **Provider Patterns** | `providers/*.py` | Change API keys, model names, endpoints |
| **Dockerfiles** | `Dockerfile*` | Modify dependencies, exposed ports |
| **CI/CD Configs** | `.github/workflows/*.yml` | Update triggers, secrets, deployment targets |
| **HTML Templates** | `templates/*.html` | Customize branding, endpoints |
| **Role Templates** | `templates/template_*.zip` | Extract and adapt for different roles |
| **Nucleus Blueprint** | `docs/NUCLEUS_STRATEGY_BLUEPRINT.md` | Adapt positioning for your product |
| **Agent Workflows** | `.agent/workflows/*.md` | Customize steps for your processes |

#### 🔴 GentleQuest-Specific (Reference Only)
| Asset | Path | Why Reference Only |
|-------|------|-------------------|
| **Crisis Detection** | `crisis_detection.py` | Geography-specific, hardcoded resources |
| **Clinical Assessments** | `providers/clinical_assessments.py` | PHQ-9/GAD-7 specific to mental health |
| **Quest System** | `scripts/seed_quests.py` | GentleQuest-specific content structure |
| **Counselor Data** | `scripts/seed_counselors.py` | University-specific counselor data |
| **Flutter Assets** | `ai_buddy_web/assets/` | Branded images and resources |
| **GentleQuest Configs** | `config/university_configs/` | University-specific configurations |

### A2. Template Libraries (Extract as Needed)
| Library | Location | Contents |
|---------|----------|----------|
| **Role Templates** | `templates/template_*.zip` | Pre-configured workspaces (AI Engineer, Researcher, Writer, Solo Founder) |
| **Email Library** | `.brain/artifacts/planning/EMAIL_LIBRARY_TEMPLATES_20260117.md` | 50+ outreach templates |
| **Workflow Templates** | `.agent/workflows/` | 17 executable workflows |
| **University Templates** | `docs/UNIVERSITY_CUSTOMIZATION_TEMPLATES.md` | Multi-university deployment patterns |
| **Strategy Playbooks** | `.brain/artifacts/planning/` | 100-day playbook, legal guide, decision frameworks |
| **Implementation Patterns** | `.brain/artifacts/implementation/` | Tested implementation strategies |
| **Go-to-Market** | `.brain/artifacts/gtm/` | GTM strategies and outreach materials |
| **Research Library** | `.brain/artifacts/research/` | SOTA benchmarks and competitive analysis |
| **Synthesis Library** | `.brain/artifacts/synthesis/` | Knowledge synthesis patterns |
| **Knowledge Base** | `.brain/knowledge/` | Anti-hallucination protocols, Oracle systems |
| **Agent Definitions** | `.brain/agents/` | Agent personas and capabilities |

### A3. Tool Libraries (Vendor as Needed)
| Tool | Location | Purpose |
|------|----------|---------|
| **Sentiment Analysis** | `tools/brain_analyze_sentiment/` | Text sentiment analysis |
| **Marketing Dashboard** | `tools/marketing-dashboard/` | Marketing metrics dashboard |
| **Nucleus HUD** | `tools/nucleus-hud/` | Real-time monitoring interface |
| **Event Tools** | `tools/omega/` | Event emission and tracking |
| **MCP Server** | `mcp-server-nucleus/` | Model Context Protocol server |
| **NAR Implementation** | `nucleus-nar/` | Nucleus Agent Runtime |
| **Provider Patterns** | `providers/` | AI, tools, and memory integration patterns |

### A4. Framework Directories (Browse for Patterns)
| Directory | Contents | Use Case |
|-----------|----------|---------|
| `.brain/artifacts/strategy/` | Strategic frameworks | Product strategy, positioning |
| `.brain/artifacts/research/` | Research methodologies | Competitive analysis, SOTA benchmarks |
| `.brain/artifacts/synthesis/` | Knowledge synthesis | Learning capture, insights |
| `.brain/artifacts/implementation/` | Implementation patterns | Tested approaches, checklists |
| `.brain/artifacts/gtm/` | Go-to-market strategies | Outreach, sales, marketing |
| `docs/` | Documentation guides | API, deployment, testing |
| `scale/` | Scaling patterns | Enterprise architecture |
| `revenue/` | Revenue systems | Billing, monetization |
| `security/` | Security patterns | Encryption, compliance |
| `ai_optimization/` | AI optimization | Cost reduction, performance |
| `config/` | Configuration patterns | Environment, university configs |
| `consciousness/` | Meta-learning system | Project intelligence |

### A5. Core Asset Map (Full)
| Asset | Path | Purpose |
|-------|------|---------|
| CONTEXT_HUB.md | /Users/lokeshgarg/ai-mvp-backend/CONTEXT_HUB.md | Spine for protocols and navigation |
| STUDIO_QUICKREF.md | /Users/lokeshgarg/ai-mvp-backend/STUDIO_QUICKREF.md | Printable quick reference |
| scaffold_experiment.sh | /Users/lokeshgarg/ai-mvp-backend/scripts/scaffold_experiment.sh | Create new experiments (copy governance, create CONTEXT.md) |
| studio_aliases.sh | /Users/lokeshgarg/ai-mvp-backend/scripts/studio_aliases.sh | Shell shortcuts (exp-new, exp-promote, exp-kill, archive-add, etc.) |
| providers/gemini.py | /Users/lokeshgarg/ai-mvp-backend/providers/gemini.py | AI provider pattern (safe to vendor) |
| providers/tools.py | /Users/lokeshgarg/ai-mvp-backend/providers/tools.py | Tool-use pattern (safe to vendor) |
| providers/memory.py | /Users/lokeshgarg/ai-mvp-backend/providers/memory.py | Memory pattern (safe to vendor) |
| scripts/ | /Users/lokeshgarg/ai-mvp-backend/scripts/ | Ops scripts & release templates (vendor selectively) |
| one_click_release.sh | /Users/lokeshgarg/ai-mvp-backend/scripts/one_click_release.sh | Multi-platform release orchestration template |
| release_android_apk.sh | /Users/lokeshgarg/ai-mvp-backend/scripts/release_android_apk.sh | Android APK build template with signing |
| release_ios_ipa.sh | /Users/lokeshgarg/ai-mvp-backend/scripts/release_ios_ipa.sh | iOS IPA build template with Xcode |
| complete_launch_checklist.sh | /Users/lokeshgarg/ai-mvp-backend/scripts/complete_launch_checklist.sh | Pre-release validation template |
| EMAIL_LIBRARY_TEMPLATES_20260117.md | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/planning/EMAIL_LIBRARY_TEMPLATES_20260117.md | 50+ outreach email templates |
| PROJECT_CONTEXT_TEMPLATE.md | /Users/lokeshgarg/ai-mvp-backend/docs/templates/PROJECT_CONTEXT_TEMPLATE.md | LLM conversation context template |
| DESIGN_JOURNAL_TEMPLATE.md | /Users/lokeshgarg/ai-mvp-backend/docs/templates/DESIGN_JOURNAL_TEMPLATE.md | Design documentation template |
| NUCLEUS_STRATEGY_BLUEPRINT.md | /Users/lokeshgarg/ai-mvp-backend/docs/NUCLEUS_STRATEGY_BLUEPRINT.md | Product strategy blueprint |
| template_*.zip | /Users/lokeshgarg/ai-mvp-backend/templates/template_*.zip | Role-based workspace templates |
| FIRST_100_DAYS_PLAYBOOK_20260117.md | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/planning/FIRST_100_DAYS_PLAYBOOK_20260117.md | 100-day execution playbook |
| WS_LEGAL_ENTITY_GUIDE_20260117.md | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/planning/WS_LEGAL_ENTITY_GUIDE_20260117.md | Legal setup guide |
| FOUNDER_DECISION_FRAMEWORKS_20260117.md | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/planning/FOUNDER_DECISION_FRAMEWORKS_20260117.md | Decision-making frameworks |
| WS_PRESS_RELEASE_TEMPLATE_20260117.md | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/planning/WS_PRESS_RELEASE_TEMPLATE_20260117.md | PR template |
| SBIR_PHASE_I_PREPARATION_GUIDE_20260117.md | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/planning/SBIR_PHASE_I_PREPARATION_GUIDE_20260117.md | Grant preparation |
| CRM_HUBSPOT_IMPLEMENTATION_20260117.md | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/planning/CRM_HUBSPOT_IMPLEMENTATION_20260117.md | CRM setup |
| scale/architecture.py | /Users/lokeshgarg/ai-mvp-backend/scale/architecture.py | Enterprise scaling patterns |
| revenue/billing_system.py | /Users/lokeshgarg/ai-mvp-backend/revenue/billing_system.py | Revenue system implementation |
| security/encryption.py | /Users/lokeshgarg/ai-mvp-backend/security/encryption.py | Security patterns |
| ai_optimization/cost_reducer.py | /Users/lokeshgarg/ai-mvp-backend/ai_optimization/cost_reducer.py | AI cost optimization |
| docs/UNIVERSITY_CUSTOMIZATION_TEMPLATES.md | /Users/lokeshgarg/ai-mvp-backend/docs/UNIVERSITY_CUSTOMIZATION_TEMPLATES.md | Multi-university deployment |
| docs/BETA_TESTING_TEMPLATES.md | /Users/lokeshgarg/ai-mvp-backend/docs/BETA_TESTING_TEMPLATES.md | Beta testing workflows |
| docs/IMPLEMENTATION_PLAN_SMOKE_FIX.md | /Users/lokeshgarg/ai-mvp-backend/docs/IMPLEMENTATION_PLAN_SMOKE_FIX.md | Implementation patterns |
| docs/DEPLOYMENT.md | /Users/lokeshgarg/ai-mvp-backend/docs/DEPLOYMENT.md | Deployment guide |
| docs/DEPLOYMENT_PROTOCOL.md | /Users/lokeshgarg/ai-mvp-backend/docs/DEPLOYMENT_PROTOCOL.md | Deployment procedures |
| docs/PROTOCOL.md | /Users/lokeshgarg/ai-mvp-backend/docs/PROTOCOL.md | Development protocols |
| docs/TESTING_GUIDE.md | /Users/lokeshgarg/ai-mvp-backend/docs/TESTING_GUIDE.md | Testing methodologies |
| docs/API_DOCUMENTATION.md | /Users/lokeshgarg/ai-mvp-backend/docs/API_DOCUMENTATION.md | API patterns |
| config/university_configs/ | /Users/lokeshgarg/ai-mvp-backend/config/university_configs/ | Configuration patterns |
| docs/schemas/ | /Users/lokeshgarg/ai-mvp-backend/docs/schemas/ | Data structure schemas |
| .agent/workflows/ | /Users/lokeshgarg/ai-mvp-backend/.agent/workflows/ | 17 executable workflows |
| .brain/artifacts/strategy/ | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/strategy/ | Strategic frameworks |
| .brain/artifacts/research/ | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/research/ | Research methodologies |
| .brain/artifacts/synthesis/ | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/synthesis/ | Knowledge synthesis |
| .brain/artifacts/implementation/ | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/implementation/ | Implementation patterns |
| .brain/artifacts/gtm/ | /Users/lokeshgarg/ai-mvp-backend/.brain/artifacts/gtm/ | Go-to-market strategies |
| .brain/knowledge/ | /Users/lokeshgarg/ai-mvp-backend/.brain/knowledge/ | Knowledge base |
| .brain/memory/ | /Users/lokeshgarg/ai-mvp-backend/.brain/memory/ | Memory patterns |
| .brain/meta/ | /Users/lokeshgarg/ai-mvp-backend/.brain/meta/ | Meta-learning |
| .brain/ledger/ | /Users/lokeshgarg/ai-mvp-backend/.brain/ledger/ | Event tracking |
| .brain/agents/ | /Users/lokeshgarg/ai-mvp-backend/.brain/agents/ | Agent definitions |
| tools/brain_analyze_sentiment/ | /Users/lokeshgarg/ai-mvp-backend/tools/brain_analyze_sentiment/ | Sentiment analysis tool |
| tools/marketing-dashboard/ | /Users/lokeshgarg/ai-mvp-backend/tools/marketing-dashboard/ | Marketing dashboard template |
| tools/nucleus-hud/ | /Users/lokeshgarg/ai-mvp-backend/tools/nucleus-hud/ | Nucleus monitoring HUD |
| tools/omega/ | /Users/lokeshgarg/ai-mvp-backend/tools/omega/ | Event emission tools |
| mcp-server-nucleus/ | /Users/lokeshgarg/ai-mvp-backend/mcp-server-nucleus/ | MCP server implementation |
| nucleus-nar/ | /Users/lokeshgarg/ai-mvp-backend/nucleus-nar/ | Nucleus NAR implementation |
| nucleus/ | /Users/lokeshgarg/ai-mvp-backend/nucleus/ | Nucleus core library |
| providers/ | /Users/lokeshgarg/ai-mvp-backend/providers/ | Provider patterns (AI, tools, memory) |
| community/ | /Users/lokeshgarg/ai-mvp-backend/community/ | Community management |
| data/ | /Users/lokeshgarg/ai-mvp-backend/data/ | Seed data |
| migrations/ | /Users/lokeshgarg/ai-mvp-backend/migrations/ | Database migrations |
| monitoring/ | /Users/lokeshgarg/ai-mvp-backend/monitoring/ | Monitoring configs |
| nginx/ | /Users/lokeshgarg/ai-mvp-backend/nginx/ | Web server configs |
| static/ | /Users/lokeshgarg/ai-mvp-backend/static/ | Static assets |
| templates/ | /Users/lokeshgarg/ai-mvp-backend/templates/ | HTML templates |
| tests/ | /Users/lokeshgarg/ai-mvp-backend/tests/ | Test suites |
| tools/ | /Users/lokeshgarg/ai-mvp-backend/tools/ | Development tools |
| deploy/ | /Users/lokeshgarg/ai-mvp-backend/deploy/ | Deployment configs |
| scripts/ops/ | /Users/lokeshgarg/ai-mvp-backend/scripts/ops/ | Operations scripts |
| scripts/schema/ | /Users/lokeshgarg/ai-mvp-backend/scripts/schema/ | Schema management |

#### A6. Vendor Strategy (Example)
```bash
# Vendoring release templates for a new app
cp ~/ai-mvp-backend/scripts/one_click_release.sh ~/experiments/my-app/vendor/
cp ~/ai-mvp-backend/scripts/release_android_apk.sh ~/experiments/my-app/vendor/
cp ~/ai-mvp-backend/scripts/release_ios_ipa.sh ~/experiments/my-app/vendor/
```
Then edit locally (app name, bundle ID, signing).

---
