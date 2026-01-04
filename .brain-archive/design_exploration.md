# 🧠 Design Thinking: Gemini CLI Grunt Worker

**Framework Stack:** Double Diamond → Diverge/Converge → SCAMPER → MVP

---

# 💎 DIAMOND 1: DISCOVER & DEFINE (The Problem)

## 🔍 DISCOVER: Diverge — What's Really Going On?

### The Surface Problem
> "I'm stuck at my Mac for all AI work."

### Digging Deeper: The 5 Whys

1. **Why stuck at Mac?** → Claude Opus/Antigravity runs here
2. **Why can't leave?** → Critical thinking + grunt work both need attention
3. **Why both at once?** → Sequential processing = bottleneck
4. **Why bottleneck?** → Single AI agent, single context, synchronous
5. **Why not parallel?** → Never built the infrastructure

### The Real Problems (Diverged)

| Problem | Type | Severity |
|:--------|:-----|:---------|
| Can't parallelize Opus + grunt work | Workflow | HIGH |
| Wasted Gemini quota | Resource | MEDIUM |
| No mobile trigger for tasks | Mobility | MEDIUM |
| Context doesn't travel between tools | Architecture | HIGH |
| Mac must be on | Infrastructure | LOW |

### User Jobs-to-be-Done

1. **Functional:** Execute multiple AI tasks in parallel
2. **Emotional:** Feel productive even when away from Mac
3. **Social:** Look like I have a "team" working for me

---

## 🎯 DEFINE: Converge — The Core Problem Statement

> **As a solo founder, I need to run grunt work (research, tests, boilerplate) on cheap/free AI in the background, so that I can focus my expensive Claude Opus time on critical thinking.**

### Constraints Identified

| Constraint | Type | Negotiable? |
|:-----------|:-----|:------------|
| Must use Gemini CLI (free quota) | Technical | No |
| Render can't reach Mac filesystem | Technical | No |
| Mac must be running for worker | Infrastructure | Maybe |
| Need Telegram trigger | UX | Yes |
| Premium model first | Quality | No |

---

# 💎 DIAMOND 2: DEVELOP & DELIVER (The Solution)

## 🌊 DEVELOP: Diverge — Alternative Architectures

### Option 1: GitHub Issues Queue (Current Plan)
```
Telegram → GitHub Issue → Mac Worker polls → Gemini CLI → Result on Issue
```
- ✅ Zero new infrastructure
- ❌ Mac must be running

### Option 2: GitHub Actions Worker
```
Telegram → GitHub Issue → GitHub Actions workflow → Gemini API → Result on Issue
```
- ✅ Runs without Mac
- ❌ No CLI, need API calls
- ❌ GitHub Actions minutes cost

### Option 3: Render Background Job
```
Telegram → Render Queue → Render Worker → Gemini API → Telegram Response
```
- ✅ All in cloud
- ❌ No Gemini CLI (no free quota)
- ❌ Ephemeral = no .brain/ context

### Option 4: Google Cloud Run
```
Telegram → Pub/Sub → Cloud Run → Gemini API (free tier) → Issue/Telegram
```
- ✅ Free tier available
- ❌ Complex setup
- ❌ No local .brain/ access

### Option 5: Ngrok Tunnel + Local Webhook
```
Telegram → Ngrok → Mac Flask server → Gemini CLI → Response
```
- ✅ Real-time, no polling
- ❌ Ngrok flaky
- ❌ Mac must be on

### Option 6: Replit Always-On Worker
```
GitHub Issue → Replit polls → Gemini API → Post result
```
- ✅ Free tier available
- ❌ No CLI
- ❌ Context sync complex

### Option 7: Dropbox/S3 File Queue
```
Telegram → Render writes to S3 → Mac daemon reads → Process → S3 result
```
- ✅ Simple file-based
- ❌ S3 costs
- ❌ Still need Mac running

### Option 8: Discord Bot
```
Discord command → Discord bot on Mac → Gemini CLI → Reply in Discord
```
- ✅ Rich formatting
- ❌ Another app to check
- ❌ Mac must be on

### Option 9: Email Trigger
```
Email to trigger@domain → Render processes → Gemini API → Reply email
```
- ✅ Works everywhere
- ❌ Slow, clunky
- ❌ No CLI

---

## 🔬 SCAMPER Analysis

### S — SUBSTITUTE
| Current | Substitute With | Result |
|:--------|:----------------|:-------|
| GitHub Issues | Google Tasks API | Faster, but less visibility |
| Telegram command | Email | Accessible but slower |
| Gemini CLI | Gemini API | Cloud-native but costs |
| Mac worker | Raspberry Pi | Always-on, low power |

**Best Substitute:** Raspberry Pi at home running 24/7 instead of Mac.

---

### C — COMBINE
| Combine | Result |
|:--------|:-------|
| Grunt worker + Nightly agent | Single scheduler handles both |
| GitHub Issues + Project board | Visual task tracking |
| Telegram + GitHub notifications | Both notify, choose one |
| Worker + Antigravity context | Shared .brain/ knowledge |

**Best Combination:** Merge grunt worker into existing nightly_agent.py as a new mode.

---

### A — ADAPT
| Adapt From | To This Use Case |
|:-----------|:-----------------|
| CI/CD pipelines | Task execution pipelines |
| GitHub Actions matrix | Parallel grunt tasks |
| Kubernetes jobs | One-shot task execution |
| AWS Lambda | Stateless task processing |

**Best Adaptation:** Use GitHub Actions as the "worker" — it already has Gemini API access patterns.

---

### M — MODIFY/MAGNIFY
| Modify | Effect |
|:-------|:-------|
| Make context richer | Better grunt work output |
| Add human-in-loop | Pause before committing changes |
| Add task chaining | "Research X, then summarize" |
| Add learning | Remember what worked |

**Best Modification:** Add task chaining — research → summarize → draft PR is a single command.

---

### P — PUT TO OTHER USES
| Use Grunt Worker For |
|:---------------------|
| Auto-review PRs during night |
| Research competitors while sleeping |
| Generate weekly reports automatically |
| Summarize RSS feeds daily |
| Pre-generate test cases for new PRs |

**Best New Use:** Nightly PR review + summarization queue.

---

### E — ELIMINATE
| Eliminate | Why | Impact |
|:----------|:----|:-------|
| Telegram trigger | Use GitHub Issues directly | Fewer moving parts |
| PyGithub on Render | Use `gh` CLI everywhere | Consistent tooling |
| Daemon mode | Use cron/launchd instead | Simpler, system-native |
| Multi-model fallback | Just use one model | Simpler, accept limits |

**Best Elimination:** Drop Telegram trigger for V1. Just use GitHub Issues directly.

---

### R — REVERSE/REARRANGE
| Reverse | Result |
|:--------|:-------|
| Worker pulls tasks → Tasks push to worker | Webhook vs polling |
| Mac as worker → Mac as controller | Trigger from Mac, run in cloud |
| Grunt work → Critical work | What if Gemini does the thinking, Claude the grunt? |

**Interesting Reversal:** What if Claude does the grunt work (via Antigravity file writes) and Gemini CLI does research? Flip the model.

---

## 🎯 DEVELOP: Converge — Selecting the Best

### Evaluation Matrix

| Option | Complexity | Free | Mac-Free | Context | Score |
|:-------|:-----------|:-----|:---------|:--------|:------|
| GitHub Issues (Mac) | Low | ✅ | ❌ | ✅ | 7/10 |
| GitHub Actions | Medium | ⚠️ | ✅ | ❌ | 6/10 |
| Raspberry Pi | Medium | ✅ | ✅* | ✅ | 8/10 |
| Nightly Agent merge | Low | ✅ | ❌ | ✅ | 8/10 |
| Just GitHub Issues | Lowest | ✅ | ❌ | ✅ | 9/10 |

### Winner: **Merged Nightly Agent + Manual GitHub Issues**

**Rationale:**
1. Already have nightly_agent.py infrastructure
2. Add `--grunt` mode that processes GitHub Issues
3. No new dependencies, no new services
4. Run manually OR via cron

---

# 🚀 MVP DEFINITION

## What's the Absolute Minimum?

### MVP = "Manual Trigger Grunt Worker"

```bash
# You run this on Mac when you want
python scripts/grunt_worker.py --process-issues
```

1. Reads open GitHub Issues with label `grunt-work`
2. Picks first one, assigns to self
3. Runs Gemini CLI with context
4. Posts result, closes issue
5. Exits (no daemon)

### NOT in MVP
- ❌ Telegram `/grunt` command
- ❌ Daemon mode
- ❌ Rate limit fallback
- ❌ Task chaining
- ❌ Context size optimization

### MVP Scope

| Component | In MVP? | Lines of Code |
|:----------|:--------|:--------------|
| `get_pending_issues()` | ✅ | 10 |
| `claim_issue()` | ✅ | 5 |
| `classify_task()` | ✅ | 15 |
| `get_context_files()` | ✅ (basic) | 10 |
| `run_gemini_cli()` | ✅ | 15 |
| `post_result()` | ✅ | 5 |
| `close_issue()` | ✅ | 3 |
| Daemon loop | ❌ | — |
| Telegram integration | ❌ | — |
| Multi-model fallback | ❌ | — |

**Total MVP: ~60 lines of Python**

---

## MVP Build Order

### Phase 0: Setup (5 min)
- [ ] Create `grunt-work` label in GitHub repo
- [ ] Verify `gh` CLI authenticated on Mac

### Phase 1: Core Script (30 min)
- [ ] Create `scripts/grunt_worker.py`
- [ ] Implement all MVP functions
- [ ] Test with a manual issue

### Phase 2: Test (10 min)
- [ ] Create test issue: "Grunt: Research top 3 mental health app competitors"
- [ ] Run worker
- [ ] Verify result comment

### Phase 3: Document (5 min)
- [ ] Add `/grunt-workflow` to .agent/workflows/
- [ ] Commit and push

---

## Success Criteria for MVP

| Criteria | Measure |
|:---------|:--------|
| Creates useful output | Result is actionable |
| Completes in < 5 min | Gemini responds fast |
| Context is relevant | Output shows it understood the project |
| Reproducible | Can run multiple times |

---

## Post-MVP Roadmap

| Feature | Value | Effort |
|:--------|:------|:-------|
| Daemon mode | Medium | 10 min |
| Telegram trigger | High | 30 min |
| Rate limit handling | Low | 15 min |
| Task chaining | High | 45 min |
| Raspberry Pi worker | High | 2 hours |

---

# 📋 FINAL DECISION

## Build This

1. **MVP script:** `scripts/grunt_worker.py` (60 lines)
2. **Trigger:** Manual CLI run
3. **Queue:** GitHub Issues with `grunt-work` label
4. **Model:** `gemini-2.0-flash-exp` (single model, no fallback)
5. **Context:** `.brain/memory/context.md` + task-specific files

## Don't Build (Yet)

- Telegram integration
- Daemon mode
- Multi-model fallback
- Cloud-based worker

---

## Estimated Time

| Phase | Time |
|:------|:-----|
| Setup | 5 min |
| MVP Script | 30 min |
| Test | 10 min |
| Document | 5 min |
| **Total** | **50 min** |

---

> **Ready to execute?**
