---
description: Apply the "GentleQuest Lens" to humanize Reddit posts (Casual, Lowercase, Vulnerable)
---

# Reddit Polish Protocol (The "Recursive" GentleQuest Lens)

This workflow applies the specific "humanizing" constraints that made GentleQuest posts successful AND checks against `REDDIT_HISTORY.md` to ensure narrative continuity.

## 0. The Recursive Check (MANDATORY)
**Before rewriting anything:**
1.  **Select Identity:** Are we `u/NucleusOS` (Builder) or `u/gentlequest_dev` (Human)?
2.  Read `nucleus-launch-internal/LAUNCH_NARRATIVE_HISTORY.md` for that specific identity.
3.  Identify the **Current Narrative Arc**.
4.  Ensure your new draft bridges from the *last* known state.

## 1. The Core Persona (Select One)

### Option A: u/NucleusOS (The Humbled Builder)
- **Voice:** Technical, Experimental, "I created a monster."
- **Context:** r/LocalLLaMA, r/ClaudeAI, r/selfhosted.
- **Narrative:** "I built a Sovereign OS, realized it was dangerous, now building safety."
- **Strategy:** Micro-Truths (2-4 lines on specific technical hurdles).

### Option B: u/gentlequest_dev (The Human)
- **Voice:** Vulnerable, Soft, "Lived Experience."
- **Context:** r/ADHD, r/Anxiety, r/Habits.
- **Narrative:** "I'm tired but trying. Here is a small thing that helped me."
- **Strategy:** Post-as-Comment (Longer personal stories).

## 2. The Transformation Rules (Universal)
- **Formatting:** Strictly lowercase. No exclamation marks. Comma splices preferred.
- **AI-Tell Prevention (CRITICAL):** 
  - **Strip all apostrophes** (e.g., "don't" -> "dont").
  - **No em-dashes** `—` or double-hyphens `--`. Use single hyphens `-` for breaks.
  - **No Version Numbers:** Remove specific release tiers like "v1.0.7" or "v2.0". They scan as corporate announcements, not builder struggles.
- **No Emojis:** Except `💀` or `😭` (rarely).

## 2. The Transformation Rules

### Rule #1: The "One-Breath" Check
If you can't say it in one breath, it's too long.
- **Bad:** "The replaying it in your head afterwards, where you analyze every word you said..."
- **Good:** "the replaying it in your head afterwards is somehow worse than the actual moment"

### Rule #2: The "Mundane Specific" Hook
Replace abstract pain with a specific, visual details.
- **Bad:** "Context switching is hard."
- **Good:** "spent 6 hours organizing my context.md and claude still asked me why i chose postgres the next day"

### Rule #3: "Show Your Work" (The Nucleus Adaptation)
When discussing technical tools, use specific numbers or JSON, but wrap it in humility.
- **Structure:** `[casual admission of struggle] + [specific proof it helped] + [question]`
- **Example:** "might be overengineered. built it because i kept losing context across 5 chats. used it daily for 6 months—948 events logged. what's your setup?"

### Rule #5: Narrative Continuity (Don't Retcon)
Check `LAUNCH_NARRATIVE_HISTORY.md`. If you claimed "Sovereign OS" last week, don't say "I'm a newbie" this week. Bridge the gap.

### Rule #6: The "Micro-Truth" Format (Nucleus Edition)
For technical builds, a 2-4 line "Progress Log" is better than a 3-paragraph essay.
- **Bad:** "I've been working on the hypervisor and here is the architecture..."
- **Good:** "spent 4 hours debugging why my hypervisor was blocking lawful `git status` calls. realized my path regex was too aggressive. regex is still the devil."

## 3. Execution Prompt (Copy/Paste this to polish text)

"Rewrite the following text using the GentleQuest Polish Protocol:
1.  **Lowercasify:** Convert to lowercase (keep proper nouns if needed for clarity).
2.  **Continuity Check:** Does this draft align with the 'Current Narrative Arc' in `LAUNCH_NARRATIVE_HISTORY.md`? If not, rewrite to bridge the gap.
3.  **De-Market:** Remove all 'announcing', 'introducing', 'solution', 'efficient'.
4.  **Humanize:** Add a 'lived experience' intro (e.g., 'i got tired of...', 'felt like...').
5.  **Shorten:** Cut to the bone. Max 2-3 sentences per block.
6.  **Proof:** If there's a claim, replace it with a specific number or JSON snippet.
7.  **Uncertainty:** End with a genuine question (not a CTA).
8.  **AI-Tell Strip:** Remove ALL apostrophes, replace all em-dashes `—` or `--` with standard `-`, and strip any version numbers (e.g., v1.0.7).
9.  **Output:** Provide the rewritten text AND a suggested update for `LAUNCH_NARRATIVE_HISTORY.md`.

**Input Text:**
[INSERT DRAFT HERE]
"

**Input Text:**
[INSERT DRAFT HERE]
"
