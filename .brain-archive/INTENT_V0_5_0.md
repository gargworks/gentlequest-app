# v0.5.0 Intent Snapshot (2026-01-05)

> **Status:** Context capture from peak design phase  
> **Purpose:** Preserve what we're thinking NOW, refine when building  
> **Can be reworked:** Yes, when v0.4.0 proves itself

---

## Feature 1: Session Management (Pathway Preservation)

### What We're Thinking Right Now

**From SATELLITE_VIEW_DESIGN_TRANSLATION.md:**
> "The system needs to understand when you're done for the day vs. just taking a break. It should preserve the 'lit neurons' - the mental map of what you were doing."

**The Problem:**
- User works on feature for 2 hours
- Gets interrupted, switches context
- Returns next day
- Has to rebuild entire mental model
- **Context loss = wasted cognitive energy**

**What This Feature Does:**
- Detects natural ending points (not time-based)
- Captures current "lit pathway" (what files open, what task active, what decisions pending)
- Stores snapshot in `.brain/sessions/`
- Restores pathway when user returns

### Why This Feature

**From Part 2 Monologue:**
> "When I come back to Nucleus work after GentleQuest, I've lost the thread. What was I building? Why did I choose this approach?"

**Alignment with North Star Principle II (Satellite View):**
> "Preserve the zoom level, the lit pathways, the context."

**Pain Points Solved:**
1. **Context rebuild tax** - Starting fresh every session
2. **Decision amnesia** - "Why did I choose this pattern?"
3. **Lost momentum** - Takes 30 min to remember where you were

### Rough Approach (Tier 1)

**Session Detection:**
```python
def detect_session_end():
    """
    Natural ending signals (NOT time-based):
    - Task marked complete in task.md
    - User says "done for today"
    - Long inactivity (>2 hours) + idle state
    """
```

**Pathway Snapshot:**
```json
{
  "session_id": "2025-01-05_nucleus_v04_work",
  "started_at": "2025-01-05T10:00:00Z",
  "ended_at": "2025-01-05T14:30:00Z",
  "focus": "Building Render Poller",
  "open_files": [
    "src/mcp_server_nucleus/tools/render_poller.py",
    "SPEC_RENDER_POLLER.md"
  ],
  "active_task": "Implementing polling loop",
  "decisions_pending": [
    "Should we poll every 30s or 60s?",
    "Timeout at 15 min or 20 min?"
  ],
  "breadcrumbs": [
    "Created spec → Started implementation → Got stuck on async polling"
  ],
  "next_steps": [
    "Research asyncio polling patterns",
    "Test with mock Render API"
  ]
}
```

**Session Resume:**
```python
def resume_session(session_id):
    """
    Restore pathway:
    1. Re-open files in order
    2. Show task status
    3. Show pending decisions
    4. Show breadcrumbs (what led here)
    5. Suggest next steps
    """
```

**CLI:**
```bash
# List recent sessions
nucleus sessions list

# Resume last session
nucleus sessions resume

# Resume specific session
nucleus sessions resume 2025-01-05_nucleus_v04_work
```

### Expand/Contract/Preserve Pattern

**From DEFINITION_OF_DONE_DESIGN_TRANSLATION.md:**

**Expand:**
- Starting new work
- Create session, begin accumulating context

**Contract:**
- Natural endpoint reached
- Save snapshot, clear working memory

**Preserve:**
- Same work, same pathway, don't snapshot yet
- Stay in flow

### Questions to Answer Later (When Building)

1. **Session granularity:** One session per day? Per feature? Per task?
2. **Storage limit:** How many sessions to keep? 30 days? 100 sessions?
3. **Cross-thread:** Should sessions track multiple parallel threads?
4. **Automatic vs manual:** Auto-detect end OR require user signal?
5. **Resume prompt:** Should system ask "Resume last session?" on startup?

### Context Sources

- [SATELLITE_VIEW_DESIGN_TRANSLATION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/SATELLITE_VIEW_DESIGN_TRANSLATION.md)
- [DEFINITION_OF_DONE_DESIGN_TRANSLATION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/DEFINITION_OF_DONE_DESIGN_TRANSLATION.md) (expand/contract/preserve)
- [SYNTHESIS_PART2_GRANULARITY_AND_VISION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/SYNTHESIS_PART2_GRANULARITY_AND_VISION.md)
- [NORTH_STAR_VISION.md Principle II](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NORTH_STAR_VISION.md)

---

## Feature 2: Brain Consolidation Automation

### What We're Thinking Right Now

**From BRAIN_CONSOLIDATION_PRINCIPLE.md:**
> "The brain doesn't keep every neuron fired forever. It consolidates during sleep, prunes redundant pathways, strengthens important ones. The digital brain should do the same."

**The Problem:**
- We've created 40 artifacts in one day
- Some are duplicates (e.g., old implementation_plan.md vs new IMPLEMENTATION_PLAN_V0_4_0.md)
- Some are obsolete (design_exploration.md, consolidation_proposal.md)
- **Artifact sprawl = harder to find relevant info**

**What This Feature Does:**
- Scans `.brain/` for redundant/obsolete artifacts
- Proposes merges (e.g., combine 3 specs into 1)
- Suggests archiving (move completed work to `.brain/archive/`)
- Runs on schedule (weekly?) or on-demand

### Why This Feature

**From BRAIN_CONSOLIDATION_PRINCIPLE (Principle XVI):**
> "Without consolidation, every artifact gets equal weight. The important ones get buried by the noise."

**Alignment with North Star Principle XIV (Execution Over Meta):**
> "Don't spend more time organizing artifacts than building features."

**Pain Points Solved:**
1. **Information buried** - Can't find the right doc
2. **Redundant artifacts** - Multiple docs say same thing
3. **Stale information** - Old plans contradict new ones

### Rough Approach (Tier 1)

**Redundancy Detection:**
```python
def detect_redundant_artifacts():
    """
    Find duplicates/overlaps:
    - Similar filenames (e.g., implementation_plan.md vs IMPLEMENTATION_PLAN_V0_4_0.md)
    - Similar content (>70% text overlap)
    - Same purpose but different dates
    """
```

**Stale Detection:**
```python
def detect_stale_artifacts():
    """
    Find outdated docs:
    - Last modified >30 days ago
    - Referenced by 0 other docs
    - Marked as "completed" in task.md
    - Status: "archived" or "superseded"
    """
```

**Merge Proposals:**
```markdown
## Consolidation Suggestions (2025-01-06)

### Merge Candidates:
1. **implementation_plan.md** + **IMPLEMENTATION_PLAN_V0_4_0.md**
   - Reason: Old plan superseded by new one
   - Suggestion: Archive old, keep new
   
2. **design_exploration.md** + **consolidation_proposal.md**
   - Reason: Both are meta-work planning docs
   - Suggestion: Merge into one "Meta Work Log"

### Archive Candidates:
1. **work_pattern_analysis.md**
   - Last modified: 20 days ago
   - Not referenced by any doc
   - Suggestion: Move to `.brain/archive/2025-01/`
```

**CLI:**
```bash
# Scan for redundancy
nucleus brain scan

# Show consolidation suggestions
nucleus brain consolidate --dry-run

# Apply suggestions
nucleus brain consolidate --apply

# Archive stale docs
nucleus brain archive --older-than=30d
```

### CEO Manages This (Not User)

**From BRAIN_CONSOLIDATION_PRINCIPLE:**
> "The Chairman (user) doesn't manage artifacts. The CEO (system) does."

**Implementation:**
- Weekly cron job (Sunday night)
- Scan brain, generate proposal
- Show proposal to user: "Found 5 merge candidates. Review?"
- User approves → CEO executes
- User skips → CEO tries again next week

### Questions to Answer Later (When Building)

1. **Similarity threshold:** 70% overlap = redundant? Or higher?
2. **Archive location:** `.brain/archive/YYYY-MM/` or flat `.brain/archive/`?
3. **Merge strategy:** Combine files OR just link + archive one?
4. **User approval:** Always required OR auto-apply for obvious cases?
5. **Restoration:** Should archived docs be searchable? Restorable?

### Context Sources

- [BRAIN_CONSOLIDATION_PRINCIPLE.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/BRAIN_CONSOLIDATION_PRINCIPLE.md)
- [NORTH_STAR_VISION.md Principle XVI](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/NORTH_STAR_VISION.md)
- [CEO_CHAIRMAN_DESIGN_TRANSLATION.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/CEO_CHAIRMAN_DESIGN_TRANSLATION.md) (CEO manages groundwork)

---

## Estimated Effort (Tier 1)

| Feature | Effort | Complexity |
|:--------|:-------|:-----------|
| Session Management | 4-6 hours | Medium (pathway capture logic) |
| Brain Consolidation | 3-4 hours | Low (file scanning, similarity) |
| **Total** | **7-10 hours** | |

---

## When to Build

**Triggers for v0.5.0:**
- v0.4.0 released and validated
- User reports context loss pain
- Artifact count >50 (currently at 40)

**Not before:** Let v0.4.0 prove Render Poller + Feature Map solve core pain first.

---

## What Could Change

**When we actually build v0.5.0, we might discover:**
1. Session snapshots need richer context (not just files)
2. Consolidation should be fully automatic (no approval)
3. Different session granularity is needed
4. Archive strategy needs to be different

**This snapshot captures 2026-01-05 thinking. Rework expected.**

---

**Captured. Ready to revisit when v0.4.0 is done.**
