# System Hierarchy & Prioritization

> **Core Revelation:** Session is the center. Brain is storage. PEFS is the safety net.

---

## The Hierarchy

```
┌─────────────────────────────────────────────────────┐
│  LEVEL 1: SESSION                                   │
│  • You + AI working together                        │
│  • task.md lives here                               │
│  • Primary. Owns its work.                          │
└─────────────────────┬───────────────────────────────┘
                      │ (you decide what persists)
                      ▼
┌─────────────────────────────────────────────────────┐
│  LEVEL 2: BRAIN (.brain/)                           │
│  • Long-term storage                                │
│  • Artifacts, events, state                         │
│  • Lives beyond any single session                  │
└─────────────────────┬───────────────────────────────┘
                      │ (auto-detection)
                      ▼
┌─────────────────────────────────────────────────────┐
│  LEVEL 3: PEFS                                      │
│  • Safety net for Brain                             │
│  • Catches unclosed items                           │
│  • Ages, reminds, suggests closure                  │
└─────────────────────────────────────────────────────┘
```

---

## What Each Level Does

| Level | Owns | Scope | Persistence |
|:------|:-----|:------|:------------|
| **Session** | Current work | This conversation | Until chat ends |
| **Brain** | Persisted work | All projects | Forever |
| **PEFS** | Detection | Brain contents only | Auto-runs daily |

---

## The Principle

**Sessions are self-contained.**

- Session starts → creates tasks in task.md
- Session works → marks tasks done
- Session ends → everything closed ✅

**Brain is for what lives beyond:**

- You explicitly move unclosed work to `.brain/`
- Or create artifacts directly in `.brain/artifacts/`
- PEFS scans ONLY `.brain/`, not session files

**PEFS is the fallback:**

- Catches `- [ ]` items you forgot in brain
- Ages them, reminds you
- You decide: close, archive, kill

---

## Prioritization Framework

### Within a Session (Level 1)

Use standard prioritization in task.md:
```
- [ ] 🔴 P1: Critical blocker (do first)
- [ ] 🟡 P2: Important (do today)
- [ ] 🟢 P3: Nice to have (do if time)
```

### In Brain/PEFS (Level 2-3)

PEFS uses **aging tiers**:

| Tier | Age | Meaning |
|:-----|:----|:--------|
| 🟢 Green | 0-2 days | Fresh, no pressure |
| 🟡 Yellow | 3-6 days | Needs attention |
| 🔴 Red | 7+ days | Mental load, close it |

### Eisenhower Matrix Integration

| | Urgent | Not Urgent |
|:--|:-------|:-----------|
| **Important** | 🔴 Do now (P1) | 🟡 Schedule (P2) |
| **Not Important** | 🟡 Delegate/quick | 🟢 Archive or kill |

**PEFS `suggested_action` maps to this:**
- `do_now` → Urgent + Important
- `schedule` → Important, needs focus
- `archive` → Not urgent, maybe later
- `kill` → Not important, delete

---

## How Prioritization Flows

```
SESSION (P1, P2, P3 in task.md)
    ↓ session ends, some items unclosed
    ↓ you move to brain

BRAIN (items in .brain/artifacts/)
    ↓ nightly scan

PEFS (aging: green → yellow → red)
    ↓ telegram reminder

YOU (close: do_now | schedule | archive | kill)
```

---

## The Simple Rule

1. **Session owns priority** for current work
2. **PEFS owns aging** for forgotten work
3. **You decide** what moves between levels

---

## What This Means for Your Work

| Scenario | What Happens |
|:---------|:-------------|
| Working in Synthesizer chat | Synthesizer's task.md tracks it |
| Chat ends, items unclosed | They stay in that session's task.md |
| You want to persist | Move explicitly to `.brain/artifacts/` |
| Something slips to brain | PEFS catches it, ages it, reminds you |
| Red tier item | Mental load signal → close it |

---

*Documented: 2026-01-06*
