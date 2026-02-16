
# REVISED PRODUCTION PLAN: Pacing & Polish
**Status:** DRAFT (Pending User Approval)

## 1. Objectives
Address user feedback on `nucleus_demo_trilogy_simple_overlay.mp4`:
1.  **Reduce Silence Gap:** Fill the ~43s silence (12s-55s) in Demo A.
2.  **Fix Voice Delivery:** Correct the robotic reading of "WHO" in `cue_06`.
3.  **Balance SFX:** Lower volume of "Amnesia" white noise; Boost volume of musical hits.

## 2. Revised Timeline (Overlay Only)
We will keep the master video intact and strictly adjust audio.

| Time | Action | Script / SFX | Change |
| :--- | :--- | :--- | :--- |
| **00:00** | Intro | "People think AI agents are magic..." + `hum_low` (Audible) | - |
| **00:08** | Naked LLMs | "That's why I don't run naked LLMs. I run Nucleus." | - |
| **00:30** | **NEW FILLER** | **"See that? It's just files. No black boxes. Auditable by default."** | **[NEW]** Matches visual of `ls -R` / file checks. |
| **00:55** | Governance | "Watch this. 'Governance Lockout'. It's not just a rule. It's physics." + `bass_drop` (**Boosted**) | - |
| **01:15** | Bridge | "Most agents have amnesia. Nucleus doesn't." + `glitch_light` (**-50% Vol**) | Lowered Vol |
| **01:22** | Recall | "Total context recall. Instantly." + `whoosh` (**Boosted**) | - |
| **01:45** | **VO FIX** | **"It remembers the actor. Who made the decision, and when."** + `chime_success` (**Boosted**) | Rephrased to avoid "W-H-O" artifact. |
| **02:10** | Power | "Now for the superpower. The Snap." + `drum_hit` (**Boosted**) | - |
| **02:25** | Snap | "I'm not writing integrations..." + `finger_snap` (**Boosted**) | - |
| **02:40** | Mesh | "Look at that. One instruction to mount the entire infrastructure." + `rising_hum` (**Boosted**) | - |
| **02:50** | God Mode | "Now I have God Mode..." + `data_noise` (**Audible**) | - |
| **03:00** | Outro | "This isn't the future. This is Nucleus." + `power_down` (**Audible**) | - |

## 3. Technical Changes
1.  **Engine Update (`simple_overlay_engine.py`):**
    - Add `volume` support to Config.
    - Increase base amplitude of synthesized SFX in `lavfi`.
2.  **Config Update:**
    - Insert `cue_02b_transparency` at 30s.
    - Update text for `cue_06_provenance`.
    - Set specific volumes: `glitch`=0.15, `bass`=0.8, others=0.6.

## 4. Execution Plan
1.  Update `SIMPLE_SCRIPT_CONFIG.json`.
2.  Run `simple_overlay_engine.py`.
3.  Verify "WHO" delivery and SFX levels.
4.  Deliver `nucleus_demo_trilogy_revised.mp4`.
