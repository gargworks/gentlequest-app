# v1.0+ Intent Snapshot (2026-01-05)

> **Status:** Context capture from peak design phase  
> **Purpose:** Preserve long-term vision while context is fresh  
> **Will evolve:** Yes, significantly as we learn from v0.4 and v0.5

---

## Feature 1: CEO Orchestrator (Multi-Agent Spawn)

### What We're Thinking Right Now

**From CEO_CHAIRMAN_DESIGN_TRANSLATION.md:**
> "The Chairman (user) sets direction. The CEO (system) spawns specialized agents to execute in parallel, escalating only when needed."

**The Problem:**
- User has to manually orchestrate: "First build feature, then test, then write docs, then deploy"
- Sequential execution wastes time
- User is doing CEO work (orchestration) instead of Chairman work (vision)

**What This Feature Does:**
- User says: "Add calm breathing mode to GentleQuest"
- CEO spawns agents in parallel:
  - **Developer Agent:** Writes Flutter code
  - **QA Agent:** Writes tests
  - **Marketing Agent:** Drafts App Store copy
  - **DevOps Agent:** Prepares deploy
- CEO manages dependencies (QA waits for Developer)
- CEO escalates to Chairman (user) only when blocked

### Why This Feature

**From Part 4 Monologue:**
> "I want to say 'build this' and have the system figure out the orchestration. I'm the Chairman, not the project manager."

**Alignment with North Star Principle III (CEO/Chairman Model):**
> "User is Chairman. System is CEO. Groundwork happens automatically."

**Pain Points Solved:**
1. **Orchestration overhead** - User manually coordinates agents
2. **Sequential waste** - Could parallelize but don't
3. **Role confusion** - User doing both CEO + Chairman work

### Rough Approach (Tier 1)

**Agent Registry:**
```json
{
  "agents": [
    {
      "id": "developer",
      "role": "Software Engineer",
      "skills": ["python", "flutter", "backend"],
      "max_concurrent": 2
    },
    {
      "id": "qa",
      "role": "QA Engineer", 
      "skills": ["testing", "e2e"],
      "dependencies": ["developer"]
    },
    {
      "id": "marketing",
      "role": "Marketing Writer",
      "skills": ["copywriting", "app-store"],
      "dependencies": []
    }
  ]
}
```

**Task Decomposition:**
```python
def decompose_feature_request(user_request):
    """
    User: "Add calm breathing mode"
    
    CEO decomposes:
    1. Developer: Build breathing widget (Flutter)
    2. Developer: Add backend endpoint (if needed)
    3. QA: Write tests (depends on Developer)
    4. Marketing: Write feature copy (parallel)
    5. DevOps: Deploy to staging (depends on QA)
    
    Returns dependency graph.
    """
```

**Parallel Execution:**
```python
async def execute_plan(task_graph):
    """
    Spawn agents in parallel:
    - Developer + Marketing start immediately
    - QA waits for Developer
    - DevOps waits for QA
    
    CEO monitors all threads, aggregates results.
    """
```

**Escalation Logic:**
```python
def should_escalate(task, context):
    """
    Escalate to Chairman if:
    - Agent stuck for >30 min
    - Ambiguous requirement ("What color for button?")
    - Trade-off decision ("Fast or accurate?")
    - Breaking change detected
    
    Don't escalate:
    - Routine implementation choices
    - Known patterns
    - Recoverable errors
    """
```

**Dashboard (Dual Product):**
```markdown
## Active Work (2025-01-05)

### GentleQuest:
- [ ] Calm breathing mode (in progress, 3/5 agents done)
  - ✅ Developer (Flutter widget done)
  - ✅ Marketing (copy written)
  - 🔄 QA (writing tests)
  - ⏳ DevOps (waiting for QA)

### Nucleus:
- [ ] v0.4.0 release (in progress, 1/3 features done)
  - ✅ Render Poller
  - 🔄 Feature Map
  - ⏳ Proof System
```

### Questions to Answer Later (When Building)

1. **Agent spawn cost:** How expensive is creating new threads? Do we reuse?
2. **Context isolation:** Can agents see each other's work?
3. **Conflict resolution:** What if Developer and QA disagree?
4. **User interruption:** Can user pause CEO, take control?
5. **Failure recovery:** If one agent fails, abort all or continue?
6. **Learning:** Does CEO get better at orchestration over time?

### Context Sources

- [CEO_CHAIRMAN_DESIGN_TRANSLATION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/CEO_CHAIRMAN_DESIGN_TRANSLATION.md)
- [CEO_ORCHESTRATION_REFINEMENT.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/CEO_ORCHESTRATION_REFINEMENT.md)
- [SYNTHESIS_PART4_CEO_ORCHESTRATION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/SYNTHESIS_PART4_CEO_ORCHESTRATION.md)
- [NORTH_STAR_VISION.md Principle III](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NORTH_STAR_VISION.md)
- [NUCLEUS_PROTOCOL_DRAFT.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NUCLEUS_PROTOCOL_DRAFT.md)

---

## Feature 2: Zoom Levels (Full Satellite View)

### What We're Thinking Right Now

**From SATELLITE_VIEW_DESIGN_TRANSLATION.md:**
> "Google Earth for your work. Zoom from 30,000 feet (all products) down to street level (single function). See lit pathways, trace history."

**The Problem:**
- User can only see one level at a time (file OR feature OR product)
- Can't zoom in/out smoothly
- Can't see "what lit up" when working
- **Lost spatial sense of the codebase**

**What This Feature Does:**
- Visual map with 4 zoom levels:
  - **Continent:** All products (GentleQuest + Nucleus)
  - **Country:** Single product (all features)
  - **City:** Single feature (all files)
  - **Street:** Single file (all functions)
- Click to zoom in/out
- Lit pathways show recent work
- Time slider shows work over time

### Why This Feature

**From Part 2 Monologue:**
> "I want to see the codebase like Google Earth. Zoom out to see the whole landscape, zoom in to see details. See where I've been, where I'm going."

**Alignment with North Star Principle II (Satellite View):**
> "Preserve zoom level, lit pathways, context across sessions."

**Pain Points Solved:**
1. **Lost in files** - Can't see forest for the trees
2. **Forgotten work** - "What did I build last week?"
3. **Context switching** - Hard to jump between levels

### Rough Approach (Tier 1)

**Data Model:**
```json
{
  "zoom_levels": {
    "continent": {
      "nodes": [
        {"id": "gentlequest", "type": "product", "children": [...]},
        {"id": "nucleus", "type": "product", "children": [...]}
      ]
    },
    "country": {
      "parent": "gentlequest",
      "nodes": [
        {"id": "crisis_detection", "type": "feature", "children": [...]},
        {"id": "calm_breathing", "type": "feature", "children": [...]}
      ]
    },
    "city": {
      "parent": "crisis_detection",
      "nodes": [
        {"id": "app/providers/safety.py", "type": "file", "children": [...]},
        {"id": "app/main.py", "type": "file", "children": [...]}
      ]
    },
    "street": {
      "parent": "app/providers/safety.py",
      "nodes": [
        {"id": "detect_crisis()", "type": "function", "lines": [10, 45]},
        {"id": "show_resources()", "type": "function", "lines": [47, 89]}
      ]
    }
  }
}
```

**Lit Pathways:**
```json
{
  "session_2025_01_05": {
    "lit_nodes": [
      "gentlequest.crisis_detection.app/providers/safety.py.detect_crisis()",
      "gentlequest.crisis_detection.app/main.py.handle_chat()"
    ],
    "intensity": {
      "detect_crisis()": 0.9,  // Heavily edited
      "handle_chat()": 0.3      // Lightly viewed
    }
  }
}
```

**UI (Terminal or Web):**
```
╔═══════════════════════════════════════╗
║         CONTINENT VIEW                ║
║                                       ║
║   [GentleQuest]  ●●●●●  (active)     ║
║   [Nucleus]      ●●○○○  (less active)║
║                                       ║
║   Click to zoom in ▼                  ║
╚═══════════════════════════════════════╝

(Click GentleQuest)

╔═══════════════════════════════════════╗
║         COUNTRY VIEW: GentleQuest     ║
║                                       ║
║   ● Crisis Detection  (lit)           ║
║   ○ Calm Breathing    (dim)           ║
║   ○ Mood Tracking     (dim)           ║
║                                       ║
║   ▲ Zoom out  |  Zoom in ▼            ║
╚═══════════════════════════════════════╝
```

**Time Dimension:**
```
Slider: [Jan 1] ────●──── [Jan 5]
                   ^now

Show lit pathways for selected date.
```

### Questions to Answer Later (When Building)

1. **Rendering:** Terminal UI (blessed, rich) or Web UI (React)?
2. **Performance:** How to handle large codebases (1000+ files)?
3. **Persistence:** Save lit pathways in `.brain/pathways/`?
4. **Auto-update:** Should pathways auto-light on file save?
5. **Filtering:** Show only changed files? Or all files?
6. **Sharing:** Can pathways be exported for team context?

### Context Sources

- [SATELLITE_VIEW_DESIGN_TRANSLATION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/SATELLITE_VIEW_DESIGN_TRANSLATION.md)
- [SYNTHESIS_PART2_GRANULARITY_AND_VISION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/SYNTHESIS_PART2_GRANULARITY_AND_VISION.md)
- [NORTH_STAR_VISION.md Principle II](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NORTH_STAR_VISION.md)

---

## Estimated Effort (Tier 1)

| Feature | Effort | Complexity |
|:--------|:-------|:-----------|
| CEO Orchestrator | 8-12 hours | High (multi-agent, dependencies) |
| Zoom Levels | 12-16 hours | Very High (UI, data model, perf) |
| **Total** | **20-28 hours** | |

**Note:** These are BIG features. Not for v1.0 unless v0.4 + v0.5 prove the foundation.

---

## When to Build

**Triggers for v1.0:**
- v0.4.0 + v0.5.0 shipped and validated
- User regularly uses Feature Map + Session Management
- Orchestration pain becomes acute (user manually coordinating agents)
- Visual navigation needed (user lost in >100 files)

**Not before:** Foundation must be solid. These are advanced features.

---

## What Will Definitely Change

**By the time we build v1.0, we'll have learned:**
1. How users actually interact with Feature Map (informs Zoom Levels)
2. Whether CEO model is even the right abstraction
3. What orchestration patterns emerge naturally
4. Whether terminal UI is sufficient or need web UI

**This snapshot is 2026-01-05 VISION. Implementation will differ.**

---

## Principle Alignment

**CEO Orchestrator aligns with:**
- Principle III (CEO/Chairman Model)
- Principle XIV (Execution Over Meta)
- Principle XV (System to Create Systems)

**Zoom Levels aligns with:**
- Principle II (Satellite View)
- Principle IX (Feature Map)
- Principle XVI (Brain Consolidation - visual organization)

---

**Captured. This is the long-term vision. Will evolve as we build v0.4 → v0.5 → v1.0.**

---

## Feature 3: Nuclear Guardrails (Immutable Constraints)

### What We're Thinking Right Now

**From Decision 004 ("Nuclear Hazard Switch"):**
> "Some constraints are non-negotiable for safety. Agents must not be allowed to override them."

**The Problem:**
- Agents optimize for local tasks (e.g., "Install this cool library") but ignore global risks ("It breaks production Python version").
- "Builder" agents often lack the "Chairman's" risk awareness.
- Currently relies on human vigilance (reading diffs).

**What This Feature Does:**
- A `guardrails.json` or `constitution.md` file that agents **cannot** modify.
- Enforced by the "Chairman" layer (Supervisor Agent) before any execution.
- If a plan violates a guardrail, it is **auto-rejected** with a hard error.

### Example Guardrails
1. **Version Lock:** `python_version == 3.9.6` (Strict)
2. **Forbidden Libs:** `no dependencies > 100MB`
3. **No-Go Zones:** `never edit /production/billing.py directly`
4. **Safety Sandwich:** `deploy_checklist.md MUST be checked before release`

### Why This Feature

**Alignment with North Star Principle III (CEO/Chairman Model):**
> "The Chairman sets the rules. The CEO executes within them."

**Pain Points Solved:**
1. **Drift:** Prevents "configuration drift" by enthusiastic agents.
2. **Safety:** Prevents catastrophic errors (like upgrading python on a legacy stack).
3. **Trust:** Allows user to give agents MORE autonomy because the "safety net" is unbreakable.

### Data Model (Draft)
```json
{
  "guardrails": [
    {
      "id": "python_lock",
      "level": "NUCLEAR",
      "condition": "python_version != 3.9.6",
      "action": "BLOCK_PR",
      "message": "Project is locked to Python 3.9.6 for production stability."
    },
    {
      "id": "billing_protection",
      "level": "CRITICAL",
      "condition": "modifies('src/billing/*')",
      "action": "REQUIRE_APPROVAL",
      "reviewer": "human"
    }
  ]
}
```

---

## Feature 8: Cross-Editor Sync (Unified Brain)

### What We're Thinking Right Now

**The Problem:**
- User works in multiple editors: Antigravity, Cursor, Windsurf, Claude Desktop
- Each editor has its own context/conversation artifacts
- Antigravity creates artifacts in `~/.gemini/antigravity/brain/UUID/`
- Cursor creates in `~/.cursor/`
- These DON'T sync automatically
- Important decisions made in one editor are invisible to others

**What This Feature Does:**
- Sync key artifacts from any IDE brain → Project `.brain/`
- Unified session management across editors
- Single source of truth for design documents

### Why This Feature

**From BRAIN_ARCHITECTURE_SYNTHESIS.md (2026-01-06):**
> "The user expected cross-layer sync because they work across Cursor, Windsurf, Antigravity, Claude Desktop. The 'brain' metaphor suggests ONE brain, but implementation has multiple."

**User Quote (2026-01-06):**
> "I didn't know this was the case. And how valuable is that? I don't know."

### Rough Approach

**Option A: Push-based sync**
```python
@mcp.tool()
def brain_sync_artifact(source_path: str, tags: list[str] = None):
    """Sync an artifact from IDE context to project .brain/"""
    # Copy to .brain/synced/{source}/{filename}
    # Add to knowledge_index.json
    # Emit sync_completed event
```

**Option B: Pull-based discovery**
```python
@mcp.tool()
def brain_discover_artifacts():
    """Scan known IDE locations for relevant artifacts"""
    # Check ~/.gemini/antigravity/brain/*/
    # Check ~/.cursor/
    # List candidates for sync
```

**Option C: Hybrid (Most Likely)**
- User marks artifacts as "sync-worthy" during session
- Nightly agent pulls marked artifacts to project .brain/
- Knowledge index updates automatically

### Implementation Priority

| Priority | Reason |
|:---------|:-------|
| **LOW for v0.x** | Only one user (founder), can manually copy |
| **MEDIUM for v1.0** | Multi-user teams would benefit |
| **HIGH if requested** | If paying users ask, prioritize |

### Current Mitigation

Added to README (2026-01-06):
> "IDE-specific context (Cursor's codebase memory, Antigravity's conversation artifacts, etc.) remains separate per editor. Manual copy is required for important documents."

---
