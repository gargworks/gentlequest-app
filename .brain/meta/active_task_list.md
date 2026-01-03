# Strategy/Docs Track - Tasks

## Current: Automated LLM Bridge ✅

- [x] Sprint 1: Nuclear Activation (COMPLETE)
- [x] Sprint 2: Hardening + Flywheel (COMPLETE)
- [x] Sprint 3: MVP Genesis (COMPLETE)
- [x] Build Hardened Cockpit v2 (COMPLETE)
- [x] Build Automated LLM Bridge:
  - [x] Create `brain_executor.py` with Gemini API
  - [x] Agent identification via system prompt files
  - [x] Context building (task + state + files)
  - [x] Response capture → event emission
  - [x] Integration with flywheel

## New: Commercial MCP Server (mcp-server-nucleus)
- [x] Initialize Project Structure
  - [x] `pyproject.toml` definition
  - [x] Directory structure (`src/mcp_server_nucleus`)
- [x] Implement Core Server (FastMCP)
- [x] Implement V1 Tools (Local Only)
  - [x] Event Tools (`emit`, `read`)
  - [x] State Tools (`get`, `update`)
  - [x] Agent Tools (`trigger`, `triggers`, `evaluate`)
  - [x] Artifact Tools (`read`, `write`, `list`)
- [x] Manual Verification (Dogfooding)
  - [x] Cold Start Verification ✅
  - [x] Development Modes Matrix Created ✅
  - [x] Naming Decision: Stick with `mcp-server-nucleus` (PyPI claimed) ✅
- [x] Package & Release Preparation
  - [x] Add LICENSE file
  - [x] Finalize README with badges
  - [x] Build package with `hatch build`
  - [x] Test install from wheel
  - [x] Publish to PyPI ✅

## Post-Launch
- [x] Create public GitHub repo ✅
- [x] Add CHANGELOG.md ✅
- [x] Clean public repo ✅
- [x] Submit to MCP.so ✅
- [x] Submit to PulseMCP ✅
- [x] Draft launch posts (Twitter/HN/Reddit) ✅
- [/] Record demo video (user editing, queued)
- [/] Post launch (queued for when video ready)

## Phase A: Complete V1 ✅
- [x] Add missing tools (10 total) ✅
- [x] Add MCP Resources (3) ✅
- [x] Add MCP Prompts (2) ✅
- [x] Write pytest tests (11 passing) ✅
- [x] Set up GitHub Actions CI ✅
- [x] Publish v0.2.0 → v0.2.1 → v0.2.2 → v0.2.3 ✅
- [x] Add nucleus-init CLI ✅
- [x] Smart Init (auto-configure Claude Desktop) ✅
- [x] Simplified config key: "nucleus" ✅

## Phase B: Validate Before You Build 🎯
> **Board Decision:** Dec 27, 2025 — Unanimous
> **Strategy:** User interviews → Templates → Pricing test → Then decide

### 🏆 Quality & Productivity Principles
> *These principles govern HOW we work, not just WHAT we build.*

#### Quality Principles
| Principle | Implementation | Status |
|:----------|:---------------|:-------|
| **Extended Thinking** | Use Opus 4.5 thinking mode for complex decisions | ✅ Active |
| **Critic Review** | Never ship without review (agent or self) | ✅ Active |
| **Tests First** | Write tests → code → fewer bugs | 🔨 Enforce |
| **Context-Aware AI** | Nucleus MCP pre-loads `.brain/` context | ✅ Active |

#### Productivity Principles
| Principle | Implementation | Status |
|:----------|:---------------|:-------|
| **Parallelism** | Gemini CLI daemon for background research | 🔨 Build |
| **Pre-loaded Context** | `.brain/` means no re-explaining project | ✅ Active |
| **Fewer Tools** | Max 3 lanes (Antigravity + Windsurf + Gemini CLI) | ✅ Active |
| **Automation** | Cron for daily digest, weekly research | 🔨 Build |

---

### Week 1-2: Discovery (Dec 28 - Jan 10)
- [ ] Conduct 5 user interviews (Reddit/Discord)
  - [ ] Find users in r/ClaudeAI, r/LocalLLaMA
  - [ ] Ask: "What's hardest about using Claude?"
  - [ ] Ask: "Would you pay for cloud backup?"
  - [ ] Ask: "Which template: Solo Founder, Developer, Researcher, Writer?"
- [x] Document `.brain/` protocol spec (1-page)
  - *Delivered:* [.brain/work_pattern_analysis.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/work_pattern_analysis.md)

### Week 3-4: Templates (Jan 11 - Jan 24)
- [ ] Ship 5 templates based on interview feedback
  - [ ] `nucleus init --template=solo-founder`
  - [ ] `nucleus init --template=developer`
  - [ ] `nucleus init --template=researcher`
  - [ ] `nucleus init --template=writer`
  - [ ] `nucleus init --template=blank`
- [ ] Add anonymous telemetry (template usage counts only)
- [ ] Publish v0.3.0 to PyPI

### Week 5-6: Pricing Validation (Jan 25 - Feb 7)
- [ ] Create "Pro waitlist" landing page ($9/mo backup)
- [ ] Offer to template users
- [ ] Measure signups

### Week 7: Decision Point (Feb 8) ⚡
- [ ] **IF 50+ waitlist signups** → Build backup feature
- [ ] **IF <10 signups** → Pivot (stay free, find other monetization)
- [ ] **IF pattern demand emerges** → Revisit Pattern Cloud

### 📊 Success Metrics
| Metric | Target | Current |
|--------|--------|---------|
| User interviews | 5 | 0 |
| Templates shipped | 5 | 0 |
| GitHub stars | 50 | ? |
| PyPI downloads | 500 | ? |
| Pro waitlist | 50 | 0 |

---

## DEFERRED: Pattern Cloud (Only if demand proven)
- Pattern Cloud backend
- ML recommendations
- Vector search (pgvector)
- Complex auth flows
- Sync daemon

## 💡 BACKLOG: Ideas for Refinement
> *Seed ideas captured during v0.2 development. Refine before implementing.*

### Response Quality / UX (Dec 27, 2025)
- **Problem:** Agent responses are jargon-heavy ("FA-001", "triggers", "event_types")
- **Impact:** Works for power users, intimidating for newcomers
- **Ideas to explore:**
  - Better MCP Prompts with plain-language guidance
  - TL;DR sections at top of artifacts
  - Persona modes (founder/developer/investor)
- **Status:** Seed idea — refine with user feedback before building

## Phase C: Monetization (After Validation)
- [ ] Pro tier: Private Sync ($9/mo)
- [ ] Stripe billing
- [ ] Team tier ($49/mo)
