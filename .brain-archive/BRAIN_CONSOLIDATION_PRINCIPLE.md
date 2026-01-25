# Brain Consolidation Principle (Meta-Layer)

> **Core Insight:** The brain doesn't just capture. It also consolidates, restructures, and prunes during sleep. Our artifact system must do the same.

---

## The Problem We're Solving

**Current State:**
- 30+ MD files in `.brain/`
- Rapid capture during sessions (RAW_MONOLOGUE_*.md, SYNTHESIS_*.md, DESIGN_*.md)
- No consolidation strategy
- Risk: Artifact sprawl, cognitive overload, lost connections

**The Question:**
> "Are we just accumulating MDs or are we also pruning neurons and consolidating knowledge like the brain does during sleep?"

---

## The Two-Phase Memory System

### Phase 1: RAM (Instant Capture)
**What:** Capture ideas on the fly without filtering  
**When:** During active sessions  
**How:** Create new MDs immediately (RAW_MONOLOGUE, SYNTHESIS)  
**Goal:** Zero loss of context

**Examples:**
- Capturing verbatim monologue
- Creating synthesis docs
- Drafting design translations

**Characteristics:**
- Fast (don't block user)
- Unstructured (capture first, organize later)
- Redundant (overlap is OK)
- Ephemeral (may be consolidated later)

---

### Phase 2: Sleep (Consolidation & Pruning)

**What:** Periodic restructuring of artifacts  
**When:** Background (CEO handles automatically)  
**How:** Merge redundant docs, prune outdated info, strengthen connections  
**Goal:** Long-term structural integrity

**The Process:**
1. **Identify Redundancy** - Which docs overlap?
2. **Merge Related** - Combine similar content
3. **Prune Outdated** - Archive or delete obsolete artifacts
4. **Strengthen Links** - Cross-reference related docs
5. **Elevate Insights** - Move critical patterns to North Star

**Examples:**
- Merge 4 RAW_MONOLOGUE files into single consolidated doc
- Update NORTH_STAR_VISION with new principles
- Archive old design drafts that were superseded
- Create index linking related artifacts

---

## The Consolidation Workflow

### When to Consolidate:

| Trigger | Action |
|:--------|:-------|
| **Session End** | Merge related docs created in session |
| **Weekly** | Prune outdated artifacts, update indexes |
| **Monthly** | Major restructuring, archive old work |
| **On Demand** | User requests "clean up brain" |

### What to Consolidate:

1. **RAW_MONOLOGUE_*.md** 
   - Keep verbatim (source code)
   - Consider archiving after synthesis extracted

2. **SYNTHESIS_*.md**
   - Merge into higher-level docs when mature
   - Or keep separate if distinct topics

3. **DESIGN_*.md**
   - Merge overlapping designs
   - Archive superseded approaches

4. **Old Artifacts**
   - implementation_plan.md (completed)
   - design_exploration.md (incorporated into other docs)
   - work_pattern_analysis.md (insights moved to North Star)

---

## Pruning Strategy (What to Delete vs Archive vs Keep)

### Keep Forever:
- ✅ NORTH_STAR_VISION.md (immutable principles)
- ✅ RAW_MONOLOGUE_*.md (source code for future recompilation)
- ✅ NUCLEUS_PROTOCOL_DRAFT.md (core architecture)
- ✅ task.md (current work tracker)

### Archive (Move to `.brain/archive/`):
- 📦 Completed implementation plans
- 📦 Superseded design docs
- 📦 Old walkthroughs (after insights extracted)

### Prune (Delete):
- ❌ Duplicate synthesis docs (after merging)
- ❌ Temporary scratch files
- ❌ Outdated drafts with no unique insights

---

## The CEO's Role in Consolidation

### Automated Background Tasks:

```python
class BrainConsolidator:
    def nightly_consolidation(self):
        """Run during idle time (user's night)."""
        
        # 1. Detect redundancy
        duplicates = detect_duplicate_content()
        
        # 2. Suggest merges
        merge_proposals = suggest_merges(duplicates)
        
        # 3. Identify dead artifacts
        stale = find_stale_artifacts(days=30)
        
        # 4. Strengthen links
        missing_links = find_missing_cross_references()
        
        # 5. Report to Chairman (low priority)
        if len(merge_proposals) > 5:
            notify_chairman(
                "Brain Consolidation Suggestions",
                f"{len(merge_proposals)} merge opportunities found",
                priority="low"
            )
```

**Key:** CEO handles this automatically. Chairman only intervenes if conflicts arise.

---

## The Two Dimensions (User's Framing)

### Dimension 1: Capture (What We're Doing Now)
- **RAM-like:** Instant, unfiltered capture
- **During sessions:** Active work
- **No loss:** Everything preserved

### Dimension 2: Consolidate (What We Need to Add)
- **Sleep-like:** Background restructuring
- **Between sessions:** Automated cleanup
- **Pruning:** Intentional forgetting of redundant/outdated info

**User's Words:**
> "Capturing ideas on the fly, then taking time to consolidate, restructure, rephrase, refactor - like pruning neurons and forgetting/learning. That dimension should drive the framework."

---

## Applying This Beyond MDs

### The Principle Applies To:

1. **Markdown Artifacts** (what we've discussed)
2. **Task States** (tasks.json - prune completed, merge related)
3. **Event Ledger** (ledger/events.jsonl - archive old events)
4. **Tools** (deprecated tools → remove from MCP)
5. **Code** (refactor, remove dead code)

**Universal Pattern:**
- **Capture fast** (don't lose context)
- **Consolidate later** (prune, merge, strengthen)
- **Automate consolidation** (CEO handles it)

---

## Implementation Roadmap (Reversibility-First)

> **Guiding Principle:** Any consolidation action MUST be reversible. Use `move`, never `delete`. See [SAFETY_AUDIT.md](file:///Users/lokeshgarg/.gemini/antigravity/brain/7c654df4-b83e-43f9-8620-f15868ec39d1/SAFETY_AUDIT.md) for audit findings.

### Phase 1: Archive Low-Value Files (Safe, Automated)
**Scope:** `.resolved.*` files (Antigravity version backups)  
**Action:** Move to `.brain/archive/resolved/`  
**Risk:** ✅ Zero (files are just version snapshots, not primary artifacts)  
**Trigger:** Add to `nightly_agent.py` for automated nightly cleanup  
**Reversibility:** Full (move back if needed)  

### Phase 2: Propose Merges (CEO-Assisted, Human-Reviewed)
**Scope:** Redundant synthesis docs, overlapping design docs  
**Action:** CEO generates merge proposals → Chairman reviews/approves  
**Risk:** 🟡 Low (human in the loop)  
**Trigger:** Weekly review session or on-demand  
**Reversibility:** Full (proposals only, no execution until approved)  

### Phase 3: Execute Approved Merges (Human-Triggered)
**Scope:** Merges approved in Phase 2  
**Action:** Combine related docs, move originals to `.brain/archive/merged/`  
**Risk:** 🟡 Low (originals preserved in archive)  
**Trigger:** Explicit command (e.g., `nucleus brain merge --execute`)  
**Reversibility:** Full (originals in archive)  

### Phase 4: Prune Archive (Deferred, Manual Only)
**Scope:** Files in `.brain/archive/` older than 90 days  
**Action:** Permanent deletion (ONLY after explicit human review)  
**Risk:** 🔴 High (irreversible)  
**Trigger:** Manual command with confirmation (e.g., `nucleus brain prune --confirm`)  
**Reversibility:** ❌ None (this is true deletion)  
**Status:** NOT IMPLEMENTED. Defer until archive is actively used.

---

## Risk Mitigation Matrix

| Phase | Action Type | Destructive? | Reversible? | Automation |
|:------|:------------|:-------------|:------------|:-----------|
| 1 | Move to archive | ❌ No | ✅ Yes | Automated |
| 2 | Generate proposals | ❌ No | ✅ Yes | Assisted |
| 3 | Merge with archive | ❌ No | ✅ Yes | Human-triggered |
| 4 | Permanent delete | ✅ Yes | ❌ No | Manual only |


---

## The Brain Consolidation Loop

```
Session (Active)
  ↓
Capture Phase (RAM)
  - Create RAW_MONOLOGUE_*.md
  - Create SYNTHESIS_*.md
  - Create DESIGN_*.md
  ↓
Session End
  ↓
Consolidation Phase (Sleep)
  - Detect redundancy
  - Merge related docs
  - Prune outdated
  - Strengthen links
  - Update North Star
  ↓
Next Session (Active)
  - Work with cleaner artifact set
  - Less cognitive load
```

---

## Success Criteria

**Good Consolidation:**
- Artifact count stays bounded (not exponential growth)
- Key insights accessible (not buried in noise)
- Links are fresh (no broken references)
- User can navigate brain easily

**Bad Consolidation:**
- Over-pruning (loss of context)
- Arbitrary deletion (no strategy)
- Manual burden (user has to do it)

---

## Linking to Other Principles

### From NORTH_STAR_VISION.md:

- **Principle III (CEO/Chairman):** CEO handles consolidation automatically
- **Principle IV (Satellite View):** Zoom levels require clean artifact hierarchy
- **Principle XIII (Forgiveness):** Don't judge accumulated artifacts, just manage them

### New Principle (XVI):
> **Brain Consolidation:** The system must consolidate artifacts periodically, like the brain during sleep. Capture fast (RAM), consolidate later (sleep), automate the process (CEO).

---

**This is the meta-layer. The system manages itself.**
