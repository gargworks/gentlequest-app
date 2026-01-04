# Problem Definition: The Lost Shipping Loop

## Core Problem (One Sentence)

**Nucleus was built to reduce cognitive load, but the queue abstraction created distance between idea and validation, breaking the dopamine loop that made shipping feel effortless in Windsurf.**

---

## The Before/After

### Before (Windsurf)
```
Idea → Shape (in chat) → Test (local) → Ship (Render) → Validate (real users) → Iterate
         ↑_______________ FAST LOOP (hours/days) ____________________↑
```
- **Dopamine trigger:** Seeing the feature live
- **Friction:** Manual (had to remember what to do next)
- **Result:** Shipped GentleQuest features regularly

### After (Nucleus)
```
Idea → Add to Queue → ... meta work ... → Task claimed → Execute → "Sprint Complete"(?)
         ↑________________________ SLOW LOOP (weeks?) _________________________↑
```
- **Dopamine trigger:** ???
- **Friction:** Ambiguity ("done" ≠ "shipped"), context loss
- **Result:** Built Nucleus, but GentleQuest features stalled

---

## Why This Happened

1. **Queue Created Distance:** The task sits in `tasks.json` while user does meta work. By the time it's "ready", the excitement is gone.
2. **Ambiguous "Done":** "Sprint complete" could mean:
   - Code written but not tested?
   - Tested locally but not deployed?
   - Deployed but not validated?
   
3. **Meta Displacement:** Building the tool took priority over using the tool.

---

## What We Need to Solve

### Must Answer (Phase 2: Define)

#### 1. What does "Ship" mean for GentleQuest?
- Is it: Push to GitHub → Deploy to Render → Test in prod?
- Should Nucleus track deploy status, not just "task done"?

#### 2. What granularity should tasks be?
**Current:** "Build safety guardrails" (too big, takes days)
**Alternative:** "Wire crisis detection to app.py" (smaller, ships in hours)?

**Trade-off:**
- Big tasks → Lose momentum, unclear progress
- Small tasks → Overhead, too many items

#### 3. How do we restore the dopamine?
What's the equivalent of "I see my feature live" in a Nucleus-managed workflow?
- Auto-deploy on task complete?
- Notification when feature is in prod?
- Weekly "Ship Report" showing what went live?

#### 4. How do we separate product vs meta work?
**Options:**
- Different task `tags` (e.g., `product`, `meta`, `urgent`)?
- Different task queues (e.g., `gentlequest_tasks.json` vs `nucleus_tasks.json`)?
- Smart filtering ("Show me only product tasks")?

---

## Clarifying Questions for User

Before we design solutions, I need to understand:

### Q1: The "Ship" Trigger
When you say you want to ship a GentleQuest feature, what's the EXACT moment you want to feel "done"?
- [ ] Code merged to GitHub?
- [ ] Render deploy succeeded?
- [ ] You tested it in prod and it works?
- [ ] Users interacted with it?

### Q2: The Right Size
Think of your recent GentleQuest work. What would have been the perfect task size?
- "Add crisis detection" (current, took weeks)  
- "Wire crisis detection to /chat endpoint" (smaller, takes hours)  
- Something else?

### Q3: The Dopamine Source
In the Windsurf loop, what gave you the most satisfaction?
- Seeing the feature work locally?
- Deploying to Render?
- Testing with a real input and seeing the result?
- All of the above?

### Q4: Meta vs Product
How should Nucleus know which tasks are "product" vs "meta"?
- Manual tagging when you create the task?
- Auto-detect based on files touched?
- Separate files entirely?

---

**Next:** Wait for user answers, then move to Phase 3 (Develop Solutions)
