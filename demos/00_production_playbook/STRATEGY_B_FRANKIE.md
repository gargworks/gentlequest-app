
# STRATEGY B: The "Human-Direct" Experiment (Frankie Model)
**Status:** ACTIVE (Primary Execution Path)
**Reference:** `LOOM_RECORDING_GUIDE_v2.md`
**Tone:** Developer-to-Developer / "Confessional" / Concrete
**Key Phrase:** "I built this because..."

## 1. Executive Summary
This strategy abandons the abstract branding of Strategy A in favor of a direct, problem-solution narrative. It frames Nucleus not as a "Sovereign Law" but as a "Developer Tool" that solves specific pain points (hallucinations, memory loss, manual integrations).

## 2. The Narrative Arch ("Frankie Framework")
*   **Hook (0:00):** The Problem ("I stopped trying to manage AI permissions manually.")
*   **Pain (0:08):** The Fear ("Hallucinated delete command.")
*   **Outcome (0:55):** Validation ("Blocked. I didn't write a regex.")
*   **Value (1:15):** Accessibility ("Most tools charge enterprise seats.")
*   **CTA (3:00):** Instruction ("pip install... do it now.")

| Time | Cue ID | Script (Spoken) | Tonal Note |
| :--- | :--- | :--- | :--- |
| **00:00** | `cue_01` | "I stopped trying to manage AI permissions manually. It's a losing game." | *Direct* |
| **00:08** | `cue_02` | "That's why I don't run naked LLMs. I run Nucleus." | *Brand* |
| **00:30** | `cue_02b` | "See these files? .env keys, config... I need to know they're safe. So I built a file-locking layer." | *Explanation* |
| **00:55** | `cue_03` | "Watch. The agent tries to delete my environment variables... and **Blocked**. It's not a suggestion. It's a hard lock." | *Validation* |
| **01:15** | `cue_04` | "Most agents also have amnesia. You close the tab, context is gone." | *Problem* |
| **01:22** | `cue_05` | "Nucleus fixes that. Total context recall." | *Solution* |
| **01:45** | `cue_06` | "It actually logs the actor. I know exactly who made the decision, and when." | *Provenance* |
| **02:10** | `cue_07` | "Now for the fun part. The Sovereign Command." | *Transition* |
| **02:25** | `cue_08` | "I don't write complex integrations anymore. I just **Snap** my fingers." | *Demo* |
| **02:40** | `cue_09` | "One instruction to mount the entire infrastructure. Stripe. Postgres. Search." | *Outcome* |
| **02:50** | `cue_10` | "It's God Mode for your local stack. Live production data... via natural language." | *Benefit* |
| **03:00** | `cue_11` | "This is Nucleus. Zero trust. Infinite memory. 100% Local." | *Outro* |

## 3. Technical Specs
*   **Engine:** `strategy_b_engine.py` (Fresh Script)
*   **Config:** `STRATEGY_B_CONFIG.json`
*   **Voice:** `en-US-Chirp3-HD-Charon` (Rate 1.05 - "YouTuber Pacing")
*   **Target Output:** `nucleus_demo_trilogy_strategy_b.mp4`

## 4. Execution Plan
1.  Configure `STRATEGY_B_CONFIG.json`.
2.  Run `strategy_b_engine.py`.
3.  Review against Strategy A (if generated) or Master.
