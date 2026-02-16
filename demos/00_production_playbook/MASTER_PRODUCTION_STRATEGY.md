
# MASTER PRODUCTION STRATEGY: The "Human-Direct" Overlay
**Status:** DRAFT (Pending Final User Sign-Off)
**Date:** 2026-02-14
**Supersedes:** `UNIFIED_PRODUCTION_PROTOCOL.md`, `COMPREHENSIVE_RECOVERY_PLAN.md`, `REVISED_PRODUCTION_PLAN.md`

## 1. Executive Summary
We are pivoting the **Narrative Tone** while keeping the **Visual Truth** locked.
*   **Visual Truth:** `nucleus_demo_master_LOCKED.mp4` (03:03). Matches the original "One-Shot" recording exactly. No edits.
*   **Audio Truth:** A **"Human-Direct"** commentary track. Less "Cinematic Trailer," more "Engineer sharing a tool."
*   **Narrative Synthesis:** Aligns with `LOOM_RECORDING_GUIDE_v2.md`: "Demonstrate outcome, not service."

## 2. The Narrative Arch ("Developer Confessional")
The script ditches marketing fluff ("Governance is Physics") for concrete engineering pain points ("I built a file-locking layer").

| Time | Cue ID | Script (Spoken) | Tonal Note |
| :--- | :--- | :--- | :--- |
| **00:00** | `cue_01` | "I built this because I was tired of my agents breaking things. They're just software. And software bugs out." | *Direct, Personal* |
| **00:08** | `cue_02` | "That's why I don't run naked LLMs. I run Nucleus." | *Brand Assertion* |
| **00:30** | `cue_02b` | **"See these files? .env keys, config... I need to know they're safe. So I built a file-locking layer."** | **[GAP FIX]** Concrete Explanation. |
| **00:55** | `cue_03` | "Watch. The agent tries to delete my environment variables... and **Blocked**. It's not a suggestion. It's a hard lock." | *Validation* |
| **01:15** | `cue_04` | "Most agents also have amnesia. You close the tab, context is gone." | *Problem Statement* |
| **01:22** | `cue_05` | "Nucleus fixes that. Total context recall." | *Solution* |
| **01:45** | `cue_06` | **"It actually logs the actor. I know exactly who made the decision, and when."** | **[VO FIX]** "Who" -> "The Actor". |
| **02:10** | `cue_07` | "Now for the fun part. The Sovereign Command." | *Transition* |
| **02:25** | `cue_08` | "I don't write complex integrations anymore. I just **Snap** my fingers." | *Demonstration* |
| **02:40** | `cue_09` | "One instruction to mount the entire infrastructure. Stripe. Postgres. Search." | *Outcome* |
| **02:50** | `cue_10` | "It's God Mode for your local stack. Live production data... via natural language." | *Benefit* |
| **03:00** | `cue_11` | "This is Nucleus. Zero trust. Infinite memory. 100% Local." | *Outro* |

## 3. Technical Specifications
### Assets
*   **Video Source:** `demos/00_production_playbook/output/nucleus_demo_master_LOCKED.mp4`
*   **Engine:** `demos/00_production_playbook/simple_overlay_engine.py` (Modified for new script)
*   **Config:** `demos/00_production_playbook/SIMPLE_SCRIPT_CONFIG.json`
*   **Output:** `demos/00_production_playbook/one_shot_output/nucleus_demo_trilogy_revised.mp4`

### Mix Profile
*   **Voice:** `en-US-Chirp3-HD-Charon`. (We keep the high-fidelity voice but change the *words* to be more casual).
*   **SFX:** Minimalist.
    *   **Glitch:** -25dB (Barely audible).
    *   **Snap:** -5dB (Prominent).
    *   **Music:** None.

## 4. Execution Rules
1.  **Do Not Edit Video:** `ffmpeg -c:v copy`.
2.  **Generate Fresh Audio:** All VO lines are new.
3.  **Verify Tone:** Ensure the TTS doesn't sound "salesy".

## 5. Sign-Off
Awaiting user confirmtion to execute `simple_overlay_engine.py` with this **Human-Direct** script.
