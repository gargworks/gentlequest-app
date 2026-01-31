# 🎯 STUDIO QUICK REFERENCE CARD
*Print this. Pin it. Use it.*

> [!LOCK]
> Canonical entrypoint is **STUDIO_MANUAL.md**. If anything here conflicts, the manual wins. Do not delete/trim without human approval. Additive edits are fine.

> [!TIP]
> When unsure, open `STUDIO_MANUAL.md` first, then follow links (CONTEXT_HUB, scaffold script, aliases).

---

## The One Command You Need

```bash
cd ~/ai-mvp-backend
./scripts/scaffold_experiment.sh idea-name
```

Then: **Open `~/experiments/idea-name` as workspace** → Tell agent: **"Read CONTEXT.md"**

---

## The Four Zones

| Zone | Path | Purpose | Rule |
|------|------|---------|------|
| **Mother** | `~/ai-mvp-backend/` | Production MVP | Don't experiment here |
| **Experiments** | `~/experiments/` | Fast exploration | Break freely |
| **Apps** | `~/apps/` | Shippable products | Git init, CI/CD |
| **Archive** | `~/archive/` | Cold storage | Don't edit |

---

## Daily Commands

| Task | Command |
|------|---------|
| New idea | `./scripts/scaffold_experiment.sh name` |
| List experiments | `ls ~/experiments/` |
| Promote to app | `mv ~/experiments/X ~/apps/X && cd ~/apps/X && git init` |
| Need code from main repo | `cp ~/ai-mvp-backend/providers/X.py ~/experiments/Y/vendor/` |

---

## Shell Aliases (Optional Power-Up)

Add to `~/.zshrc`:
```bash
source ~/ai-mvp-backend/scripts/studio_aliases.sh
```

Then use:
- `exp-new idea` → Create experiment
- `exp-list` → List experiments
- `exp-promote idea` → Promote to app
- `studio-help` → Full reference

---

## Golden Rules

✅ **DO**
- Copy, don't symlink
- Kill experiments that aren't working
- Tell agents "Read CONTEXT.md first"
- Vendor code into `vendor/`

❌ **DON'T**
- Nest experiments inside Mother Repo
- Edit files in `~/archive/`
- Use multi-root workspaces with Mother + experiment
- Import relative paths like `../../ai-mvp-backend`

---

## Key Files

| File | Purpose |
|------|---------|
| `CONTEXT_HUB.md` | The "spine" - maps all protocols |
| `STUDIO_MANUAL.md` | Full documentation |
| `STUDIO_QUICKREF.md` | This card |
| `scripts/scaffold_experiment.sh` | The magic command |
| `scripts/studio_aliases.sh` | Shell power-ups |

---

## Experiment Folder Structure

```
~/experiments/my-idea/
├── CONTEXT.md        ← Agent reads this first
├── brief.md          ← Your plan (edit immediately)
├── AGENTS.md         ← Copied governance
├── PROTOCOL.md       ← Copied governance
├── src/              ← Your code
├── vendor/           ← Copied libraries (read-only)
└── docs/             ← Documentation
```

---

## Workflow Lifecycle

```
IDEA → scaffold → ~/experiments/X → build → decide
                                              │
                              ┌───────────────┼───────────────┐
                              ↓               ↓               ↓
                            KILL           PIVOT          PROMOTE
                         (delete)       (keep iterating)  (→ ~/apps/X)
```

---

*v1.0.0 | Jan 18, 2026*
